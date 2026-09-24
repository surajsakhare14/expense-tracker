"""Business logic for the transaction ledger with atomic balance updates.

This service owns the financial transaction boundary. Every balance-affecting
operation follows the same shape:

1. lock the affected account row (``SELECT ... FOR UPDATE``);
2. validate all business rules;
3. create / update / soft-delete the transaction record;
4. adjust ``account.current_balance`` by the balance delta;
5. flush;
6. commit exactly once.

Any exception rolls the whole operation back, so the transaction record and the
account balance can never drift apart. Atomicity is enforced here explicitly and
does not depend on the pytest savepoint fixture.
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.account import Account
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository

_ZERO = Decimal(0)
_CREDIT_CARD = "CREDIT_CARD"

_VALID_TYPES = {t.value for t in TransactionType}
_VALID_STATUSES = {s.value for s in TransactionStatus}
_CATEGORY_TYPES = {
    TransactionType.INCOME.value: "INCOME",
    TransactionType.EXPENSE.value: "EXPENSE",
}


class TransactionService:
    """Transaction validation, balance effects, and user-scoped operations."""

    def __init__(self, session: Session):
        self.session = session
        self.transactions = TransactionRepository(session)
        self.accounts = AccountRepository(session)
        self.categories = CategoryRepository(session)

    # ------------------------------------------------------------------ reads
    def get_transaction(self, transaction_id: str, user_id: str) -> Transaction:
        transaction = self.transactions.get_transaction(transaction_id, user_id)
        if transaction is None:
            raise self._not_found()
        return transaction

    def list_transactions(
        self,
        user_id: str,
        *,
        account_id: str | None = None,
        category_id: str | None = None,
        transaction_type: str | None = None,
        status: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Transaction], int]:
        offset = (page - 1) * page_size
        items = self.transactions.list_transactions(
            user_id,
            account_id=account_id,
            category_id=category_id,
            transaction_type=transaction_type,
            status=status,
            date_from=date_from,
            date_to=date_to,
            limit=page_size,
            offset=offset,
        )
        total = self.transactions.count_transactions(
            user_id,
            account_id=account_id,
            category_id=category_id,
            transaction_type=transaction_type,
            status=status,
            date_from=date_from,
            date_to=date_to,
        )
        return items, total

    # --------------------------------------------------------------- mutations
    def create_transaction(
        self,
        user_id: str,
        *,
        account_id: str,
        transaction_type: str,
        amount: Decimal | str | int | float,
        transaction_date: datetime | None = None,
        category_id: str | None = None,
        description: str | None = None,
        merchant_name: str | None = None,
        status: str = TransactionStatus.COMPLETED.value,
    ) -> Transaction:
        amount = self._to_decimal(amount)
        transaction_date = transaction_date or datetime.now(timezone.utc)
        try:
            account = self.accounts.get_account_for_update(account_id, user_id)
            if account is None:
                raise self._account_not_found()
            if account.archived_at is not None:
                raise self._archived_rejected()

            self._validate_status(status)
            self._validate_rules(user_id, transaction_type, amount, category_id)

            transaction = self.transactions.create_transaction(
                account_id=account_id,
                category_id=category_id,
                transaction_type=transaction_type,
                status=status,
                amount=amount,
                transaction_date=transaction_date,
                description=description,
                merchant_name=merchant_name,
            )
            effect = self._balance_effect(
                account.account_type, transaction_type, status, amount
            )
            self._apply_delta(account, effect)

            self.session.flush()
            self.session.commit()
            return transaction
        except Exception:
            self.session.rollback()
            raise

    def update_transaction(
        self, transaction_id: str, user_id: str, values: dict[str, object]
    ) -> Transaction:
        try:
            original = self.transactions.get_transaction(transaction_id, user_id)
            if original is None:
                raise self._not_found()

            # The transaction stays on its original account; moving funds between
            # accounts is a transfer, not an edit.
            if "account_id" in values and values["account_id"] != original.account_id:
                raise self._account_immutable()

            account = self.accounts.get_account_for_update(original.account_id, user_id)
            if account is None:
                raise self._account_not_found()

            new_type = str(values.get("transaction_type", original.transaction_type))
            new_status = str(values.get("status", original.status))
            new_amount = (
                self._to_decimal(values["amount"])
                if "amount" in values
                else original.amount
            )
            new_category_id = (
                values["category_id"] if "category_id" in values else original.category_id
            )

            self._validate_status(new_status)
            self._validate_rules(user_id, new_type, new_amount, new_category_id)

            old_effect = self._balance_effect(
                account.account_type,
                original.transaction_type,
                original.status,
                original.amount,
            )
            new_effect = self._balance_effect(
                account.account_type, new_type, new_status, new_amount
            )

            update_values = self._normalize_update_values(values, new_amount)
            self.transactions.update_transaction(original, update_values)
            self._apply_delta(account, new_effect - old_effect)

            self.session.flush()
            self.session.commit()
            return original
        except Exception:
            self.session.rollback()
            raise

    def delete_transaction(self, transaction_id: str, user_id: str) -> None:
        try:
            original = self.transactions.get_transaction(transaction_id, user_id)
            if original is None:
                raise self._not_found()

            account = self.accounts.get_account_for_update(original.account_id, user_id)
            if account is None:
                raise self._account_not_found()

            old_effect = self._balance_effect(
                account.account_type,
                original.transaction_type,
                original.status,
                original.amount,
            )
            self.transactions.soft_delete_transaction(original)
            # Reversing an effective transaction removes its contribution.
            self._apply_delta(account, -old_effect)

            self.session.flush()
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    # ----------------------------------------------------------- balance logic
    @staticmethod
    def _balance_effect(
        account_type: str, transaction_type: str, status: str, amount: Decimal
    ) -> Decimal:
        """Signed change a transaction applies to ``account.current_balance``.

        Only ``COMPLETED`` transactions move balance. For asset accounts income
        adds and expense subtracts. A credit card is a liability whose
        ``current_balance`` is the amount owed, so the income/expense signs flip:
        an expense increases what is owed and income (e.g. a refund) reduces it.
        Opening balance and (signed) balance adjustment apply their raw amount to
        the stored balance regardless of account type.
        """
        if status != TransactionStatus.COMPLETED.value:
            return _ZERO
        if transaction_type in (
            TransactionType.OPENING_BALANCE.value,
            TransactionType.BALANCE_ADJUSTMENT.value,
        ):
            return amount

        is_liability = account_type == _CREDIT_CARD
        if transaction_type == TransactionType.INCOME.value:
            return -amount if is_liability else amount
        if transaction_type == TransactionType.EXPENSE.value:
            return amount if is_liability else -amount
        return _ZERO

    @staticmethod
    def _apply_delta(account: Account, delta: Decimal) -> None:
        if delta == _ZERO:
            return
        account.current_balance = account.current_balance + delta
        account.updated_at = datetime.now(timezone.utc)

    # -------------------------------------------------------------- validation
    def _validate_rules(
        self, user_id: str, transaction_type: str, amount: Decimal, category_id: str | None
    ) -> None:
        if transaction_type not in _VALID_TYPES:
            raise self._invalid_type()

        if transaction_type in (TransactionType.INCOME.value, TransactionType.EXPENSE.value):
            if amount <= _ZERO:
                raise self._invalid_amount("Amount must be greater than zero.")
            if category_id is None:
                raise self._category_required()
            category = self.categories.get_visible_category(category_id, user_id)
            if category is None:
                raise self._category_not_found()
            if category.category_type != _CATEGORY_TYPES[transaction_type]:
                raise self._category_type_mismatch()
        else:  # OPENING_BALANCE / BALANCE_ADJUSTMENT
            if amount == _ZERO:
                raise self._invalid_amount("Amount must not be zero.")
            if category_id is not None:
                raise self._category_not_allowed()

    @staticmethod
    def _validate_status(status: str) -> None:
        if status not in _VALID_STATUSES:
            raise AppException(
                code="TRANSACTION_INVALID_STATUS",
                message="Transaction status is not valid.",
                status_code=422,
            )

    @staticmethod
    def _normalize_update_values(
        values: dict[str, object], new_amount: Decimal
    ) -> dict[str, object]:
        allowed = (
            "transaction_type",
            "status",
            "category_id",
            "transaction_date",
            "description",
            "merchant_name",
        )
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
            code="TRANSACTION_NOT_FOUND",
            message="Transaction could not be found.",
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
    def _archived_rejected() -> AppException:
        return AppException(
            code="ACCOUNT_ARCHIVED",
            message="Archived accounts cannot receive new financial activity.",
            status_code=409,
        )

    @staticmethod
    def _account_immutable() -> AppException:
        return AppException(
            code="TRANSACTION_ACCOUNT_IMMUTABLE",
            message="A transaction cannot be moved to a different account.",
            status_code=409,
        )

    @staticmethod
    def _invalid_type() -> AppException:
        return AppException(
            code="TRANSACTION_INVALID_TYPE",
            message="Transaction type is not valid.",
            status_code=422,
        )

    @staticmethod
    def _invalid_amount(message: str) -> AppException:
        return AppException(
            code="TRANSACTION_INVALID_AMOUNT", message=message, status_code=422
        )

    @staticmethod
    def _category_required() -> AppException:
        return AppException(
            code="TRANSACTION_CATEGORY_REQUIRED",
            message="Income and expense transactions require a category.",
            status_code=422,
        )

    @staticmethod
    def _category_not_allowed() -> AppException:
        return AppException(
            code="TRANSACTION_CATEGORY_NOT_ALLOWED",
            message="Opening balance and adjustment transactions must not have a category.",
            status_code=422,
        )

    @staticmethod
    def _category_not_found() -> AppException:
        return AppException(
            code="CATEGORY_NOT_FOUND",
            message="Category could not be found.",
            status_code=404,
        )

    @staticmethod
    def _category_type_mismatch() -> AppException:
        return AppException(
            code="TRANSACTION_CATEGORY_TYPE_MISMATCH",
            message="Category type must match the transaction type.",
            status_code=422,
        )
