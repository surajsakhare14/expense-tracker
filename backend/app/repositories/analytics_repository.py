"""Read-only data access for the analytics domain.

Analytics never write and never commit; this repository only issues SELECTs
against the financial source-of-truth tables (accounts, transactions, transfers,
categories). It centralises the two rules every analytics query must share —
analytics eligibility and per-user scoping — so later M4 chunks can build
concrete aggregations (sums, group-bys, trends) on top of a correct base query
instead of repeating the filter logic across six reports.

M4 eligibility and classification (classification is layered on by callers):
- Eligible rows are ``COMPLETED`` and not soft-deleted; ``PENDING``,
  ``CANCELLED`` and soft-deleted rows are excluded.
- ``INCOME`` -> income and ``EXPENSE`` -> expense.
- ``OPENING_BALANCE`` is excluded from income and expense.
- ``BALANCE_ADJUSTMENT`` is a separate adjustment metric, excluded from income
  and expense.
- Transfers are never income or expense; credit-card payments are transfers and
  must not be double-counted as expenses. Transfer reads scope by the owning
  account per query (source and/or destination) since a transfer references two
  accounts.
- Everything is scoped to the authenticated user through the owning account,
  because transactions and transfers carry no direct ``user_id``.
"""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.category import Category
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction


class AnalyticsRepository:
    """Shared, read-only query building blocks for analytics (always user-scoped)."""

    # Only these transaction types participate in income/expense analytics;
    # OPENING_BALANCE and BALANCE_ADJUSTMENT are handled as separate metrics.
    INCOME_EXPENSE_TYPES = (TransactionType.INCOME.value, TransactionType.EXPENSE.value)

    def __init__(self, session: Session):
        self.session = session

    def base_transaction_query(self, user_id: str) -> Select:
        """Return the base SELECT of analytics-eligible transactions for a user.

        Joins each transaction to its owning account for user scoping and applies
        the ``COMPLETED`` + not-soft-deleted eligibility rule. Type classification,
        date-range/account filters and aggregation are layered on by the query
        methods added in later M4 chunks; this method performs no calculation.
        """
        return (
            select(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .where(*self._scope_conditions(user_id))
        )

    def overview_totals(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        account_id: str | None = None,
    ) -> dict[str, Decimal]:
        """Aggregate income, expense and balance-adjustment totals for a period.

        Sums are computed in PostgreSQL (no rows are loaded into Python) over the
        analytics-eligible rows only, classifying by transaction type:

        - ``INCOME`` -> ``total_income`` (amounts are positive).
        - ``EXPENSE`` -> ``total_expense`` (amounts are positive).
        - ``BALANCE_ADJUSTMENT`` -> ``net_balance_adjustment`` (amounts are already
          signed by the model, so they are summed as-is, never ``abs()``-ed).

        ``OPENING_BALANCE`` matches no bucket and is therefore excluded from every
        figure; transfers live in a separate table and never appear here. The
        date range is inclusive of both ends (see ``_period_bounds``). Each total
        defaults to ``Decimal("0")`` when nothing matches — never ``None``. This
        method issues a single read-only ``SELECT`` and never commits.
        """
        start_dt, end_dt = self._period_bounds(start_date, end_date)
        conditions = [
            *self._scope_conditions(user_id),
            Transaction.transaction_date >= start_dt,
            Transaction.transaction_date < end_dt,
        ]
        if account_id is not None:
            conditions.append(Transaction.account_id == account_id)

        statement = (
            select(
                self._sum_of(TransactionType.INCOME.value).label("total_income"),
                self._sum_of(TransactionType.EXPENSE.value).label("total_expense"),
                self._sum_of(TransactionType.BALANCE_ADJUSTMENT.value).label(
                    "net_balance_adjustment"
                ),
            )
            .select_from(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .where(*conditions)
        )
        row = self.session.execute(statement).one()
        return {
            "total_income": self._as_decimal(row.total_income),
            "total_expense": self._as_decimal(row.total_expense),
            "net_balance_adjustment": self._as_decimal(row.net_balance_adjustment),
        }

    def income_by_category(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        account_id: str | None = None,
    ) -> dict:
        """Sum eligible ``INCOME`` for a period, grouped by category.

        Only ``INCOME`` rows participate; ``EXPENSE``, ``OPENING_BALANCE`` and
        ``BALANCE_ADJUSTMENT`` are excluded, as are transfers (a separate table).
        See ``_amount_by_category`` for the shared eligibility, scoping, grouping
        and precision rules. Returns ``{"total_income", "categories"}`` where each
        category is ``{"category_id", "category_name", "amount"}``.
        """
        breakdown = self._amount_by_category(
            user_id, TransactionType.INCOME.value, start_date, end_date, account_id
        )
        return {"total_income": breakdown["total"], "categories": breakdown["categories"]}

    def expense_by_category(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        account_id: str | None = None,
    ) -> dict:
        """Sum eligible ``EXPENSE`` for a period, grouped by category.

        Only ``EXPENSE`` rows participate; ``INCOME``, ``OPENING_BALANCE`` and
        ``BALANCE_ADJUSTMENT`` are excluded, as are transfers (credit-card
        payments are transfers and must never be counted as expense). See
        ``_amount_by_category`` for the shared eligibility, scoping, grouping and
        precision rules. Returns ``{"total_expense", "categories"}`` where each
        category is ``{"category_id", "category_name", "amount"}``.
        """
        breakdown = self._amount_by_category(
            user_id, TransactionType.EXPENSE.value, start_date, end_date, account_id
        )
        return {"total_expense": breakdown["total"], "categories": breakdown["categories"]}

    def expense_category_breakdown(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        account_id: str | None = None,
    ) -> dict:
        """Sum and count eligible ``EXPENSE`` for a period, grouped by category.

        The category report is ``expense_by_category`` plus a per-group
        ``transaction_count`` (kept as its own method so the income/expense
        reports, which need no counts, are unaffected). Only ``EXPENSE`` rows
        participate; ``INCOME``, ``OPENING_BALANCE`` and ``BALANCE_ADJUSTMENT`` are
        excluded, as are transfers (credit-card payments are transfers and must
        never count as expense). Eligibility, user scoping and the inclusive window
        are the shared analytics rules (see ``_scope_conditions`` and
        ``_period_bounds``); grouping, summing and counting all happen in
        PostgreSQL — no rows are loaded into Python. The join to ``categories`` is a
        ``LEFT`` join so a row without a category still forms a group
        (``category_id``/``category_name`` are then ``None``); the caller labels
        that bucket. Rows are ordered by amount descending then category name
        ascending, and ``total_expense`` is the exact ``Decimal`` sum of the
        groups. Read-only; never commits.
        """
        start_dt, end_dt = self._period_bounds(start_date, end_date)
        conditions = [
            *self._scope_conditions(user_id),
            Transaction.transaction_type == TransactionType.EXPENSE.value,
            Transaction.transaction_date >= start_dt,
            Transaction.transaction_date < end_dt,
        ]
        if account_id is not None:
            conditions.append(Transaction.account_id == account_id)

        amount = func.sum(Transaction.amount)
        statement = (
            select(
                Transaction.category_id.label("category_id"),
                Category.name.label("category_name"),
                amount.label("amount"),
                func.count(Transaction.id).label("transaction_count"),
            )
            .select_from(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .join(Category, Transaction.category_id == Category.id, isouter=True)
            .where(*conditions)
            .group_by(Transaction.category_id, Category.name)
            .order_by(amount.desc(), Category.name.asc())
        )
        categories = [
            {
                "category_id": row.category_id,
                "category_name": row.category_name,
                "amount": self._as_decimal(row.amount),
                "transaction_count": row.transaction_count,
            }
            for row in self.session.execute(statement).all()
        ]
        total_expense = sum((c["amount"] for c in categories), Decimal("0"))
        return {"total_expense": total_expense, "categories": categories}

    def monthly_trends(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        account_id: str | None = None,
    ) -> list[dict]:
        """Aggregate eligible income/expense per calendar month and currency.

        Groups the analytics-eligible ``INCOME``/``EXPENSE`` rows in the inclusive
        window into one bucket per (month, currency) and returns the conditional
        ``Decimal`` sums for each — all grouping and summing happen in PostgreSQL,
        so no raw transactions are loaded into Python and there are no N+1 queries.
        The month bucket is derived with ``date_trunc('month', ...)`` after
        normalising ``transaction_date`` to UTC (``timezone('UTC', ...)``) so month
        assignment never depends on the database session's time zone, matching the
        half-open UTC window used elsewhere (see ``_period_bounds``); it is rendered
        as ``YYYY-MM``. Currency comes from the owning account and is grouped on so
        different currencies are never summed together. ``OPENING_BALANCE``,
        ``BALANCE_ADJUSTMENT`` and transfers (a separate table) never contribute.

        The result is *sparse* — only (month, currency) pairs that actually have
        eligible activity appear; the service fills the empty months across the
        requested range. Each row is
        ``{"period", "currency", "income", "expense"}`` with money as ``Decimal``.
        Read-only; never commits.
        """
        start_dt, end_dt = self._period_bounds(start_date, end_date)
        period = func.to_char(
            func.date_trunc("month", func.timezone("UTC", Transaction.transaction_date)),
            "YYYY-MM",
        )
        conditions = [
            *self._scope_conditions(user_id),
            Transaction.transaction_type.in_(self.INCOME_EXPENSE_TYPES),
            Transaction.transaction_date >= start_dt,
            Transaction.transaction_date < end_dt,
        ]
        if account_id is not None:
            conditions.append(Transaction.account_id == account_id)

        statement = (
            select(
                period.label("period"),
                Account.currency.label("currency"),
                self._sum_of(TransactionType.INCOME.value).label("income"),
                self._sum_of(TransactionType.EXPENSE.value).label("expense"),
            )
            .select_from(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .where(*conditions)
            .group_by(period, Account.currency)
        )
        return [
            {
                "period": row.period,
                "currency": row.currency,
                "income": self._as_decimal(row.income),
                "expense": self._as_decimal(row.expense),
            }
            for row in self.session.execute(statement).all()
        ]

    def _amount_by_category(
        self,
        user_id: str,
        transaction_type: str,
        start_date: date,
        end_date: date,
        account_id: str | None = None,
    ) -> dict:
        """Sum eligible transactions of one type for a period, grouped by category.

        Shared by the income and expense reports. Applies the analytics
        eligibility (``COMPLETED`` + not soft-deleted) and user scoping, filters
        to ``transaction_type`` inside the inclusive window (see
        ``_period_bounds``) and optional ``account_id``, and groups/sums entirely
        in PostgreSQL (``GROUP BY`` category) — no per-row amounts are loaded into
        Python. The join to ``categories`` is a ``LEFT`` join so a row without a
        category still forms a group (``category_id``/``category_name`` are then
        ``None``); the caller labels that bucket. ``total`` is the exact
        ``Decimal`` sum of the returned groups. Read-only; never commits.
        """
        start_dt, end_dt = self._period_bounds(start_date, end_date)
        conditions = [
            *self._scope_conditions(user_id),
            Transaction.transaction_type == transaction_type,
            Transaction.transaction_date >= start_dt,
            Transaction.transaction_date < end_dt,
        ]
        if account_id is not None:
            conditions.append(Transaction.account_id == account_id)

        amount = func.sum(Transaction.amount)
        statement = (
            select(
                Transaction.category_id.label("category_id"),
                Category.name.label("category_name"),
                amount.label("amount"),
            )
            .select_from(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .join(Category, Transaction.category_id == Category.id, isouter=True)
            .where(*conditions)
            .group_by(Transaction.category_id, Category.name)
            .order_by(amount.desc(), Category.name.asc())
        )
        categories = [
            {
                "category_id": row.category_id,
                "category_name": row.category_name,
                "amount": self._as_decimal(row.amount),
            }
            for row in self.session.execute(statement).all()
        ]
        total = sum((c["amount"] for c in categories), Decimal("0"))
        return {"total": total, "categories": categories}

    @staticmethod
    def _scope_conditions(user_id: str) -> list:
        """Eligibility + user scoping shared by every analytics query."""
        return [
            Account.user_id == user_id,
            Transaction.status == TransactionStatus.COMPLETED.value,
            Transaction.deleted_at.is_(None),
        ]

    @staticmethod
    def _sum_of(transaction_type: str):
        """SUM of ``amount`` restricted to one transaction type, ``0`` when empty."""
        return func.coalesce(
            func.sum(
                case(
                    (Transaction.transaction_type == transaction_type, Transaction.amount),
                    else_=0,
                )
            ),
            0,
        )

    @staticmethod
    def _period_bounds(start_date: date, end_date: date) -> tuple[datetime, datetime]:
        """Return the half-open UTC datetime window ``[start_00:00, (end+1)_00:00)``.

        ``transaction_date`` is a timezone-aware timestamp while the filters are
        calendar dates, so both ends are made inclusive by extending the upper
        bound to the start of the day after ``end_date``. UTC is used explicitly
        so the window does not depend on the database session's time zone.
        """
        start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
        return start_dt, end_dt

    @staticmethod
    def _as_decimal(value) -> Decimal:
        """Coerce an aggregate result to ``Decimal`` without ever going through float."""
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
