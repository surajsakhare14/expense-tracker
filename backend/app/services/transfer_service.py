"""Business logic for account-to-account transfers with atomic balance updates.

This service owns the financial transaction boundary for transfers. Every
effective transfer touches two account balances, so both account rows are locked
(``SELECT ... FOR UPDATE``) in a deterministic order before any validation or
mutation, then the whole operation commits exactly once. Any exception rolls
everything back, so neither balance and no transfer record is left partially
changed. Atomicity is enforced here explicitly and does not depend on the pytest
savepoint fixture.
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.account import Account
from app.models.enums import TransferStatus
from app.models.transfer import Transfer
from app.repositories.account_repository import AccountRepository
from app.repositories.transfer_repository import TransferRepository

_ZERO = Decimal(0)
_CREDIT_CARD = "CREDIT_CARD"
_VALID_STATUSES = {s.value for s in TransferStatus}


class TransferService:
    """Transfer validation, balance effects, and user-scoped operations."""

    def __init__(self, session: Session):
        self.session = session
        self.transfers = TransferRepository(session)
        self.accounts = AccountRepository(session)

    # ------------------------------------------------------------------ reads
    def get_transfer(self, transfer_id: str, user_id: str) -> Transfer:
        transfer = self.transfers.get_transfer(transfer_id, user_id)
        if transfer is None:
            raise self._not_found()
        return transfer

    def list_transfers(
        self,
        user_id: str,
        *,
        account_id: str | None = None,
        status: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Transfer], int]:
        offset = (page - 1) * page_size
        items = self.transfers.list_transfers(
            user_id,
            account_id=account_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            limit=page_size,
            offset=offset,
        )
        total = self.transfers.count_transfers(
            user_id,
            account_id=account_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
        )
        return items, total

    # --------------------------------------------------------------- mutations
    def create_transfer(
        self,
        user_id: str,
        *,
        source_account_id: str,
        destination_account_id: str,
        amount: Decimal | str | int | float,
        transfer_date: datetime | None = None,
        description: str | None = None,
        status: str = TransferStatus.COMPLETED.value,
    ) -> Transfer:
        amount = self._to_decimal(amount)
        transfer_date = transfer_date or datetime.now(timezone.utc)
        try:
            self._validate_status(status)
            if amount <= _ZERO:
                raise self._invalid_amount()
            if source_account_id == destination_account_id:
                raise self._same_account()

            source, destination = self._lock_pair(
                source_account_id, destination_account_id, user_id
            )
            self._require_active(source)
            self._require_active(destination)
            self._require_same_currency(source, destination)

            transfer = self.transfers.create_transfer(
                source_account_id=source_account_id,
                destination_account_id=destination_account_id,
                amount=amount,
                status=status,
                transfer_date=transfer_date,
                description=description,
            )
            self._apply(source, destination, amount, status, direction=1)

            self.session.flush()
            self.session.commit()
            return transfer
        except Exception:
            self.session.rollback()
            raise

    def update_transfer(
        self, transfer_id: str, user_id: str, values: dict[str, object]
    ) -> Transfer:
        try:
            original = self.transfers.get_transfer(transfer_id, user_id)
            if original is None:
                raise self._not_found()

            # Source/destination stay fixed for this milestone: re-pointing a
            # transfer would require locking a second account pair atomically.
            for field in ("source_account_id", "destination_account_id"):
                if field in values and values[field] != getattr(original, field):
                    raise self._accounts_immutable()

            source, destination = self._lock_pair(
                original.source_account_id, original.destination_account_id, user_id
            )

            new_status = str(values.get("status", original.status))
            new_amount = (
                self._to_decimal(values["amount"])
                if "amount" in values
                else original.amount
            )
            self._validate_status(new_status)
            if new_amount <= _ZERO:
                raise self._invalid_amount()

            # Reverse the old effect, then apply the new effect on both sides.
            self._apply(source, destination, original.amount, original.status, direction=-1)
            self._apply(source, destination, new_amount, new_status, direction=1)

            self.transfers.update_transfer(
                original, self._normalize_update_values(values, new_amount)
            )

            self.session.flush()
            self.session.commit()
            return original
        except Exception:
            self.session.rollback()
            raise

    def delete_transfer(self, transfer_id: str, user_id: str) -> None:
        try:
            original = self.transfers.get_transfer(transfer_id, user_id)
            if original is None:
                raise self._not_found()

            source, destination = self._lock_pair(
                original.source_account_id, original.destination_account_id, user_id
            )
            # Reverse both effects; a non-effective transfer contributes zero.
            self._apply(source, destination, original.amount, original.status, direction=-1)
            self.transfers.soft_delete_transfer(original)

            self.session.flush()
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    # ------------------------------------------------------------- locking
    def _lock_pair(
        self, source_id: str, destination_id: str, user_id: str
    ) -> tuple[Account, Account]:
        """Lock both accounts in a deterministic (sorted-id) order to avoid deadlock."""
        first_id, second_id = sorted((source_id, destination_id))
        locked: dict[str, Account | None] = {
            first_id: self.accounts.get_account_for_update(first_id, user_id),
            second_id: self.accounts.get_account_for_update(second_id, user_id),
        }
        source = locked[source_id]
        destination = locked[destination_id]
        if source is None or destination is None:
            raise self._account_not_found()
        return source, destination

    # ----------------------------------------------------------- balance logic
    def _apply(
        self, source: Account, destination: Account, amount: Decimal, status: str, direction: int
    ) -> None:
        """Apply (direction=1) or reverse (direction=-1) a transfer's balance effect."""
        source_effect = self._source_effect(source.account_type, status, amount)
        destination_effect = self._destination_effect(
            destination.account_type, status, amount
        )
        self._apply_delta(source, direction * source_effect)
        self._apply_delta(destination, direction * destination_effect)

    @staticmethod
    def _source_effect(account_type: str, status: str, amount: Decimal) -> Decimal:
        """Effect on the source account. Money leaves an asset (-); a credit card
        is a liability, so sending from it increases what is owed (+)."""
        if status != TransferStatus.COMPLETED.value:
            return _ZERO
        return amount if account_type == _CREDIT_CARD else -amount

    @staticmethod
    def _destination_effect(account_type: str, status: str, amount: Decimal) -> Decimal:
        """Effect on the destination account. Money arrives at an asset (+); a
        payment into a credit card reduces what is owed (-)."""
        if status != TransferStatus.COMPLETED.value:
            return _ZERO
        return -amount if account_type == _CREDIT_CARD else amount

    @staticmethod
    def _apply_delta(account: Account, delta: Decimal) -> None:
        if delta == _ZERO:
            return
        account.current_balance = account.current_balance + delta
        account.updated_at = datetime.now(timezone.utc)

    # -------------------------------------------------------------- validation
    def _require_active(self, account: Account) -> None:
        if account.archived_at is not None:
            raise self._archived_rejected()

    def _require_same_currency(self, source: Account, destination: Account) -> None:
        if source.currency != destination.currency:
            raise AppException(
                code="TRANSFER_CURRENCY_MISMATCH",
                message="Source and destination accounts must use the same currency.",
                status_code=422,
            )

    @staticmethod
    def _validate_status(status: str) -> None:
        if status not in _VALID_STATUSES:
            raise AppException(
                code="TRANSFER_INVALID_STATUS",
                message="Transfer status is not valid.",
                status_code=422,
            )

    @staticmethod
    def _normalize_update_values(
        values: dict[str, object], new_amount: Decimal
    ) -> dict[str, object]:
        allowed = ("status", "transfer_date", "description")
        update_values: dict[str, object] = {
            field: values[field] for field in allowed if field in values
        }
        if "amount" in values:
            update_values["amount"] = new_amount
        return update_values

    @staticmethod
    def _to_decimal(amount: Decimal | str | int | float) -> Decimal:
        if isinstance(amount, Decimal):
            return amount
        return Decimal(str(amount))

    # ------------------------------------------------------------------ errors
    @staticmethod
    def _not_found() -> AppException:
        return AppException(
            code="TRANSFER_NOT_FOUND",
            message="Transfer could not be found.",
            status_code=404,
        )

    @staticmethod
    def _account_not_found() -> AppException:
        return AppException(
            code="ACCOUNT_NOT_FOUND",
            message="Account could not be found.",
            status_code=404,
        )

    @staticmethod
    def _same_account() -> AppException:
        return AppException(
            code="TRANSFER_SAME_ACCOUNT",
            message="Source and destination accounts must be different.",
            status_code=422,
        )

    @staticmethod
    def _invalid_amount() -> AppException:
        return AppException(
            code="TRANSFER_INVALID_AMOUNT",
            message="Transfer amount must be greater than zero.",
            status_code=422,
        )

    @staticmethod
    def _archived_rejected() -> AppException:
        return AppException(
            code="ACCOUNT_ARCHIVED",
            message="Archived accounts cannot participate in new transfers.",
            status_code=409,
        )

    @staticmethod
    def _accounts_immutable() -> AppException:
        return AppException(
            code="TRANSFER_ACCOUNTS_IMMUTABLE",
            message="A transfer's source and destination accounts cannot be changed.",
            status_code=409,
        )
