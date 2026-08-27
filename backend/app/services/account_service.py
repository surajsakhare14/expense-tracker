"""Business logic for financial accounts."""

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.repositories.account_repository import AccountRepository
from app.schemas.account import (
    AccountCreateRequest,
    AccountDataResponse,
    AccountListResponse,
    AccountResponse,
    AccountUpdateRequest,
)


class AccountService:
    """Account validation and user-scoped operations."""

    def __init__(self, session: Session):
        self.repository = AccountRepository(session)

    def create_account(self, user_id: str, request: AccountCreateRequest) -> AccountDataResponse:
        if self.repository.has_active_name(user_id, request.name):
            raise AppException(
                code="ACCOUNT_NAME_ALREADY_EXISTS",
                message="An active account with this name already exists.",
                status_code=409,
            )
        account = self.repository.create_account(
            user_id=user_id,
            name=request.name,
            account_type=request.account_type,
            institution_name=request.institution_name,
            currency=request.currency,
        )
        return AccountDataResponse(data=self._to_response(account))

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
            raise AppException(
                code="ACCOUNT_NAME_ALREADY_EXISTS",
                message="An active account with this name already exists.",
                status_code=409,
            )
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
