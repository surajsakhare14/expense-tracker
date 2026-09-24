"""Enumerations for financial event domains (transactions and transfers)."""

from enum import StrEnum


class TransactionType(StrEnum):
    """The kind of financial event a transaction records."""

    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    OPENING_BALANCE = "OPENING_BALANCE"
    BALANCE_ADJUSTMENT = "BALANCE_ADJUSTMENT"


class TransactionStatus(StrEnum):
    """Lifecycle status controlling whether a transaction affects balance."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TransferStatus(StrEnum):
    """Lifecycle status controlling whether a transfer affects balances."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
