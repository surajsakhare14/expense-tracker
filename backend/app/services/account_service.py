"""Business logic for financial accounts."""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.enums import TransactionStatus, TransactionType
from app.repositories.account_repository import AccountRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.account import (
    AccountCreateRequest,
    AccountDataResponse,
    AccountListResponse,
    AccountResponse,
    AccountUpdateRequest,
)

_ZERO = Decimal(0)
_LOCKED_ON_ACTIVITY = ("account_type", "currency")


class AccountService:
    """Account validation and user-scoped operations."""

    def __init__(self, session: Session):
        self.session = session
        self.repository = AccountRepository(session)
        self.transactions = TransactionRepository(session)

    def create_account(self, user_id: str, request: AccountCreateRequest) -> AccountDataResponse:
        if self.repository.has_active_name(user_id, request.name):
            raise self._name_conflict()

        opening_balance = request.opening_balance
        if opening_balance is None or opening_balance == _ZERO:
            account = self.repository.create_account(
                user_id=user_id,
                name=request.name,
                account_type=request.account_type,
                institution_name=request.institution_name,
                currency=request.currency,
            )
            return AccountDataResponse(data=self._to_response(account))

        account = self._create_with_opening_balance(user_id, request, opening_balance)
        return AccountDataResponse(data=self._to_response(account))

    def _create_with_opening_balance(
        self, user_id: str, request: AccountCreateRequest, opening_balance: Decimal
    ):
        """Create the account and its OPENING_BALANCE transaction in one commit.

        An OPENING_BALANCE transaction applies its raw signed amount to the
        balance regardless of account type, so the account's ``current_balance``
        equals the opening balance once created. Any failure rolls back both the
        account and the transaction, leaving nothing partially created.
        """
        try:
            account = self.repository.add_account(
                user_id=user_id,
                name=request.name,
                account_type=request.account_type,
                institution_name=request.institution_name,
                currency=request.currency,
            )
            self.transactions.create_transaction(
                account_id=account.id,
                category_id=None,
                transaction_type=TransactionType.OPENING_BALANCE.value,
                status=TransactionStatus.COMPLETED.value,
                amount=opening_balance,
                transaction_date=datetime.now(timezone.utc),
                description="Opening balance",
            )
            account.current_balance = opening_balance
            self.session.flush()
            self.session.commit()
            return account
        except Exception:
            self.session.rollback()
            raise

    def list_accounts(self, user_id: str, include_archived: bool = False) -> AccountListResponse:
        accounts = self.repository.list_accounts(user_id, include_archived=include_archived)
        return AccountListResponse(data=[self._to_response(account) for account in accounts])

    def get_account(
        self, account_id: str, user_id: str, include_archived: bool = False
    ) -> AccountDataResponse:
        account = self.repository.get_account(
            account_id, user_id, include_archived=include_archived
        )
        if not account:
            raise self._not_found()
        return AccountDataResponse(data=self._to_response(account))

    def update_account(
        self, account_id: str, user_id: str, request: AccountUpdateRequest
    ) -> AccountDataResponse:
        account = self.repository.get_account(account_id, user_id)
        if not account:
            raise self._not_found()
        values = request.model_dump(exclude_unset=True)
        if "name" in values and self.repository.has_active_name(
            user_id, values["name"], account_id
        ):
            raise self._name_conflict()

        # account_type and currency lock once the account has financial activity;
        # only check when the request actually changes one of them.
        locked_changes = [
            field
            for field in _LOCKED_ON_ACTIVITY
            if field in values and values[field] != getattr(account, field)
        ]
        if locked_changes and self.repository.has_financial_activity(account_id):
            raise self._activity_locked(locked_changes)

        account = self.repository.update_account(account, values)
        return AccountDataResponse(data=self._to_response(account))

    def archive_account(self, account_id: str, user_id: str) -> None:
        account = self.repository.get_account(account_id, user_id)
        if not account:
            raise self._not_found()
        self.repository.archive_account(account)

    @staticmethod
    def _to_response(account) -> AccountResponse:
        return AccountResponse.model_validate(account, from_attributes=True)

    @staticmethod
    def _not_found() -> AppException:
        return AppException(
            code="ACCOUNT_NOT_FOUND",
            message="Account could not be found.",
            status_code=404,
        )

    @staticmethod
    def _name_conflict() -> AppException:
        return AppException(
            code="ACCOUNT_NAME_ALREADY_EXISTS",
            message="An active account with this name already exists.",
            status_code=409,
        )

    @staticmethod
    def _activity_locked(fields: list[str]) -> AppException:
        joined = " and ".join(fields)
        return AppException(
            code="ACCOUNT_ACTIVITY_LOCKED",
            message=f"Account {joined} cannot be changed after financial activity exists.",
            status_code=409,
        )
