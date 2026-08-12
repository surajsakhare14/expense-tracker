# 04_Database_Design.md

# MoneyScope — Database Design

> **Version:** 1.0.0
> **Status:** Database Architecture Definition
> **Database:** PostgreSQL
> **ORM:** SQLAlchemy 2.x
> **Migration Tool:** Alembic
> **Primary Currency:** INR
> **Database Philosophy:** Relational, user-scoped, auditable, financially consistent

---

# 1. Purpose

This document defines the PostgreSQL database architecture for MoneyScope V1.

It covers:

- Core entities
- Tables
- Relationships
- Primary keys
- Foreign keys
- Constraints
- Indexes
- Monetary data types
- Transaction modeling
- Account modeling
- Budget modeling
- Goal modeling
- Investment modeling
- Notification modeling
- Import modeling
- Audit considerations
- Soft deletion
- Data ownership
- Database transaction rules

This document is the source of truth for database implementation.

The database implementation should follow this document unless an architectural decision is explicitly updated.

---

# 2. Database Goals

The database must provide:

## Correctness

Financial records must remain internally consistent.

## User Isolation

A user must never access another user's financial records.

## Auditability

Important financial operations should be traceable.

## Extensibility

Future bank, UPI, investment, and AI integrations should not require a complete schema redesign.

## Query Performance

Common queries such as:

- Monthly spending
- Recent transactions
- Category spending
- Account balance
- Budget utilization
- Goal progress

must be efficiently queryable.

## Data Integrity

Critical relationships should be enforced at the PostgreSQL level rather than relying only on application code.

---

# 3. Database Philosophy

MoneyScope follows these principles:

1. PostgreSQL is the source of truth.
2. Financial amounts use fixed precision.
3. UUIDs are preferred for public identifiers.
4. User ownership is enforced server-side.
5. Foreign keys are used extensively.
6. Important uniqueness rules are enforced by the database.
7. Derived metrics are not the primary source of truth.
8. Soft deletion is preferred for user-visible financial records where appropriate.
9. Database transactions are required for multi-step financial mutations.
10. Indexes should support real query patterns rather than being added indiscriminately.

---

# 4. High-Level Entity Relationship

```text
                              ┌──────────────┐
                              │    users     │
                              └──────┬───────┘
                                     │
              ┌──────────────────────┼───────────────────────┐
              │                      │                       │
              ▼                      ▼                       ▼
       ┌─────────────┐       ┌─────────────┐        ┌──────────────┐
       │ user_profile│       │ preferences │        │ notifications│
       └─────────────┘       └─────────────┘        └──────────────┘

                                     │
                                     ▼
                              ┌─────────────┐
                              │  accounts   │
                              └──────┬──────┘
                                     │
                                     ▼
                              ┌─────────────┐
                              │ transactions│
                              └──────┬──────┘
                                     │
                    ┌────────────────┼─────────────────┐
                    │                │                 │
                    ▼                ▼                 ▼
              ┌──────────┐    ┌────────────┐    ┌─────────────┐
              │categories│    │  merchants │    │import_jobs  │
              └──────────┘    └────────────┘    └─────────────┘


users
 │
 ├──────────────► budgets
 │                   │
 │                   ▼
 │              budget_categories
 │
 ├──────────────► goals
 │                   │
 │                   ▼
 │              goal_contributions
 │
 ├──────────────► investment_holdings
 │
 ├──────────────► liabilities
 │
 ├──────────────► reports
 │
 └──────────────► linked_providers


news_sources
     │
     ▼
news_articles
     │
     ▼
news_tags
```

---

# 5. Core Tables

MoneyScope V1 contains the following major database domains.

## Identity

- users
- user_profiles
- user_preferences
- refresh_tokens

## Financial Accounts

- accounts
- linked_providers
- liabilities

## Transactions

- transactions
- categories
- merchants
- transaction_import_jobs
- transaction_import_rows

## Budgeting

- budgets
- budget_categories

## Goals

- goals
- goal_contributions

## Investments

- investment_holdings
- investment_snapshots

## Notifications

- notifications
- notification_preferences

## Reports

- financial_reports

## News

- news_sources
- news_articles
- news_tags
- news_article_tags

## Audit

- audit_logs

---

# 6. Primary Key Strategy

UUIDs should be used as primary keys for user-facing domain entities.

Example:

```text
user_id
account_id
transaction_id
goal_id
investment_id
```

Recommended PostgreSQL type:

```text
UUID
```

Recommended generation strategy:

```text
gen_random_uuid()
```

or application-generated UUIDs.

The exact implementation should be finalized during SQLAlchemy setup.

---

# 7. Common Fields

Most domain tables should follow a common timestamp convention.

```text
id
created_at
updated_at
```

Example:

```text
id UUID PRIMARY KEY
created_at TIMESTAMPTZ NOT NULL
updated_at TIMESTAMPTZ NOT NULL
```

For entities supporting archival:

```text
deleted_at TIMESTAMPTZ NULL
```

or:

```text
archived_at TIMESTAMPTZ NULL
```

---

# 8. User Table

## Table

```text
users
```

Purpose:

Stores authentication identity.

### Fields

```text
id                  UUID PK
email               VARCHAR
password_hash       VARCHAR
is_active           BOOLEAN
email_verified      BOOLEAN
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

### Constraints

```text
email NOT NULL
email UNIQUE
password_hash NOT NULL
```

Email uniqueness should be case-insensitive.

Recommended PostgreSQL approach:

```text
CITEXT
```

or a functional unique index using normalized email.

---

# 9. User Profile

## Table

```text
user_profiles
```

Purpose:

Stores presentation and personal finance preferences that are not authentication credentials.

### Fields

```text
id                  UUID PK
user_id             UUID FK → users.id
display_name        VARCHAR
avatar_url           VARCHAR NULL
currency             VARCHAR
timezone             VARCHAR
created_at           TIMESTAMPTZ
updated_at           TIMESTAMPTZ
```

### Relationship

```text
users 1 ─── 1 user_profiles
```

### Constraints

```text
user_id UNIQUE
currency NOT NULL
timezone NOT NULL
```

---

# 10. User Preferences

## Table

```text
user_preferences
```

Purpose:

Stores application behavior preferences.

### Fields

```text
id                          UUID PK
user_id                     UUID FK
theme                       VARCHAR
overspending_alerts_enabled BOOLEAN
bill_reminders_enabled      BOOLEAN
goal_notifications_enabled  BOOLEAN
monthly_report_enabled      BOOLEAN
created_at                  TIMESTAMPTZ
updated_at                  TIMESTAMPTZ
```

### Relationship

```text
users 1 ─── 1 user_preferences
```

---

# 11. Refresh Tokens

## Table

```text
refresh_tokens
```

Purpose:

Stores refresh-token metadata for secure session management.

### Fields

```text
id                  UUID PK
user_id             UUID FK
token_hash          VARCHAR
expires_at          TIMESTAMPTZ
revoked_at          TIMESTAMPTZ NULL
created_at          TIMESTAMPTZ
```

### Important

The raw refresh token should NOT be stored.

Store a secure hash instead.

---

# 12. Accounts

## Table

```text
accounts
```

Purpose:

Represents where money is stored or managed.

### Account Types

```text
BANK
CASH
CREDIT_CARD
WALLET
UPI_ACCOUNT
OTHER
```

### Fields

```text
id                  UUID PK
user_id             UUID FK
name                VARCHAR
account_type        VARCHAR / ENUM
institution_name    VARCHAR NULL
currency            VARCHAR
current_balance     NUMERIC(19,4)
is_active           BOOLEAN
archived_at         TIMESTAMPTZ NULL
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

### Relationship

```text
users 1 ─── N accounts
```

---

# 13. Account Balance Strategy

The database must distinguish between:

## Authoritative transaction history

and

## Cached/current account balance

The preferred V1 approach is:

```text
Transactions
      ↓
Balance Calculation
      ↓
Account Balance
```

A `current_balance` field may be stored for fast reads, but it must not become an independently editable source of truth without corresponding transaction logic.

Whenever balance-affecting transactions are created, modified, or deleted, the balance update must happen atomically.

---

# 14. Linked Providers

## Table

```text
linked_providers
```

Purpose:

Represents external financial/payment providers associated with the user.

Examples:

```text
Google Pay
PhonePe
Paytm
Bank
Future Account Aggregator
```

### Fields

```text
id                  UUID PK
user_id             UUID FK
provider_type       VARCHAR
provider_name       VARCHAR
display_name        VARCHAR NULL
status              VARCHAR
external_reference  VARCHAR NULL
linked_at           TIMESTAMPTZ
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

### Important

Provider linkage must not require storing sensitive provider credentials unless an official integration requires it.

Secrets should be stored securely outside ordinary application tables.

---

# 15. Categories

## Table

```text
categories
```

Purpose:

Provides transaction classification.

### Fields

```text
id                  UUID PK
user_id             UUID FK NULL
name                VARCHAR
category_type       VARCHAR
parent_id           UUID FK → categories.id NULL
is_system           BOOLEAN
is_active           BOOLEAN
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

### Category Types

```text
EXPENSE
INCOME
```

### System Categories

System categories have:

```text
is_system = true
user_id = NULL
```

User-specific categories have:

```text
is_system = false
user_id = user.id
```

---

# 16. Merchants

## Table

```text
merchants
```

Purpose:

Stores normalized merchant information.

### Fields

```text
id                  UUID PK
name                VARCHAR
normalized_name     VARCHAR
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

A transaction may preserve the original merchant text separately.

This allows:

```text
Original:
SWIGGY ONLINE

Normalized:
Swiggy
```

---

# 17. Transactions

## Table

```text
transactions
```

This is one of the most important tables in MoneyScope.

### Fields

```text
id                      UUID PK
user_id                 UUID FK
account_id              UUID FK
category_id             UUID FK NULL
merchant_id             UUID FK NULL

amount                  NUMERIC(19,4)
transaction_type        VARCHAR
direction               VARCHAR

merchant_name           VARCHAR NULL
description             TEXT NULL

payment_provider        VARCHAR NULL

occurred_at             TIMESTAMPTZ

source                  VARCHAR
external_reference      VARCHAR NULL

import_job_id           UUID FK NULL

is_deleted              BOOLEAN
deleted_at              TIMESTAMPTZ NULL

created_at              TIMESTAMPTZ
updated_at              TIMESTAMPTZ
```

---

# 18. Transaction Types

Recommended values:

```text
EXPENSE
INCOME
TRANSFER
INVESTMENT
REFUND
```

---

# 19. Transaction Direction

Recommended values:

```text
DEBIT
CREDIT
```

Examples:

### Expense

```text
type = EXPENSE
direction = DEBIT
```

### Salary

```text
type = INCOME
direction = CREDIT
```

### Transfer Out

```text
type = TRANSFER
direction = DEBIT
```

### Transfer In

```text
type = TRANSFER
direction = CREDIT
```

---

# 20. Transfer Modeling

MoneyScope must not treat transfers as expenses.

Example:

```text
HDFC → ICICI
₹10,000
```

This represents movement of money, not spending.

V1 may initially represent transfer sides using linked transactions.

Future schema can introduce:

```text
transfer_id
```

to explicitly pair both sides.

Recommended future-compatible design:

```text
transactions
    │
    └── transfer_group_id
```

Both transaction records share the same transfer group.

---

# 21. Transaction Source

Recommended values:

```text
MANUAL
CSV
BANK_IMPORT
UPI_IMPORT
API
```

V1 actively supports:

```text
MANUAL
CSV
```

Future sources should not require redesigning the transaction table.

---

# 22. Transaction External Reference

External systems may provide identifiers.

Example:

```text
external_reference
```

This helps detect duplicate transactions during imports.

Uniqueness should normally be scoped by source/provider/account rather than globally.

Example conceptual uniqueness:

```text
(user_id, account_id, source, external_reference)
```

Only apply this constraint where the external reference is guaranteed to be reliable.

---

# 23. Transaction Import Jobs

## Table

```text
transaction_import_jobs
```

Purpose:

Tracks CSV and future import operations.

### Fields

```text
id                  UUID PK
user_id             UUID FK
source_type         VARCHAR
file_name           VARCHAR
status              VARCHAR

total_rows          INTEGER
accepted_rows       INTEGER
rejected_rows       INTEGER
duplicate_rows      INTEGER

error_summary       JSONB NULL

started_at          TIMESTAMPTZ NULL
completed_at        TIMESTAMPTZ NULL

created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

### Status

```text
PENDING
PROCESSING
COMPLETED
PARTIAL
FAILED
CANCELLED
```

---

# 24. Transaction Import Rows

## Table

```text
transaction_import_rows
```

Purpose:

Stores row-level import processing results when required for diagnostics.

### Fields

```text
id                  UUID PK
import_job_id       UUID FK
row_number          INTEGER
raw_data             JSONB
status              VARCHAR
error_code          VARCHAR NULL
error_message       TEXT NULL
transaction_id      UUID FK NULL
created_at          TIMESTAMPTZ
```

This allows the UI to explain:

```text
Row 27:
Invalid date format
```

without exposing internal exceptions.

---

# 25. Budgets

## Table

```text
budgets
```

Purpose:

Stores user budgeting periods.

### Fields

```text
id                  UUID PK
user_id             UUID FK
name                VARCHAR
period_type         VARCHAR
start_date          DATE
end_date            DATE
amount              NUMERIC(19,4)
is_active            BOOLEAN
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

### Period Types

Initial:

```text
MONTHLY
```

Future:

```text
WEEKLY
YEARLY
CUSTOM
```

---

# 26. Budget Categories

## Table

```text
budget_categories
```

Purpose:

Allows a budget to have category-level limits.

### Fields

```text
id                  UUID PK
budget_id           UUID FK
category_id         UUID FK
amount              NUMERIC(19,4)
created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

### Constraint

A category should only appear once within the same budget.

Recommended unique constraint:

```text
(budget_id, category_id)
```

---

# 27. Budget Utilization

Budget utilization is derived.

Example:

```text
Budget:
₹30,000

Eligible Expenses:
₹21,000

Utilization:
70%
```

Do not store:

```text
utilization_percentage
```

as the primary truth.

Calculate it from:

```text
budget amount
+
eligible transactions
```

Caching may be added later for performance.

---

# 28. Goals

## Table

```text
goals
```

Purpose:

Represents user financial objectives.

### Fields

```text
id                  UUID PK
user_id             UUID FK

name                VARCHAR
goal_type           VARCHAR

target_amount       NUMERIC(19,4)
saved_amount        NUMERIC(19,4)

deadline            DATE NULL

status              VARCHAR

icon_key            VARCHAR NULL
color_key           VARCHAR NULL

created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
archived_at         TIMESTAMPTZ NULL
```

---

# 29. Goal Status

Recommended values:

```text
ACTIVE
COMPLETED
PAUSED
ARCHIVED
```

---

# 30. Goal Contributions

## Table

```text
goal_contributions
```

Purpose:

Records individual goal funding events.

### Fields

```text
id                      UUID PK
goal_id                 UUID FK
amount                  NUMERIC(19,4)
contributed_at          TIMESTAMPTZ
note                    TEXT NULL
source_transaction_id   UUID FK NULL
created_at              TIMESTAMPTZ
updated_at              TIMESTAMPTZ
```

---

# 31. Goal Balance Strategy

A key database decision:

Do not rely solely on manually editable `goals.saved_amount`.

The authoritative source should preferably be:

```text
goal_contributions
        ↓
SUM(amount)
        ↓
Goal Saved Amount
```

A cached `saved_amount` may be maintained for performance.

If both are stored, updates must happen atomically.

---

# 32. Investments

## Table

```text
investment_holdings
```

Purpose:

Stores user investment holdings.

### Fields

```text
id                  UUID PK
user_id             UUID FK

name                VARCHAR
asset_type          VARCHAR

quantity            NUMERIC(24,8) NULL
average_cost        NUMERIC(19,4) NULL

invested_amount     NUMERIC(19,4)
current_value       NUMERIC(19,4)

broker_name         VARCHAR NULL

status              VARCHAR

created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
archived_at         TIMESTAMPTZ NULL
```

---

# 33. Investment Asset Types

Initial values:

```text
STOCK
MUTUAL_FUND
FIXED_DEPOSIT
GOLD
OTHER
```

Future types can include:

```text
ETF
BOND
CRYPTO
NPS
PPF
```

These should only be added when supported by the product.

---

# 34. Investment Snapshots

## Table

```text
investment_snapshots
```

Purpose:

Stores historical portfolio values.

### Fields

```text
id                  UUID PK
user_id             UUID FK
snapshot_date       DATE
total_invested      NUMERIC(19,4)
total_value         NUMERIC(19,4)
profit_loss         NUMERIC(19,4)
created_at          TIMESTAMPTZ
```

### Constraint

One portfolio snapshot per user per date:

```text
(user_id, snapshot_date) UNIQUE
```

This supports:

```text
12 Month Portfolio Chart
```

without reconstructing historical values from every transaction.

---

# 35. Liabilities

## Table

```text
liabilities
```

Purpose:

Represents money the user owes.

### Fields

```text
id                  UUID PK
user_id             UUID FK

name                VARCHAR
liability_type      VARCHAR

principal_amount    NUMERIC(19,4)
outstanding_amount  NUMERIC(19,4)

interest_rate       NUMERIC(8,4) NULL

due_date            DATE NULL

status              VARCHAR

created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
archived_at         TIMESTAMPTZ NULL
```

### Initial Types

```text
CREDIT_CARD
LOAN
OTHER
```

This supports future net-worth calculations.

---

# 36. Net Worth

Net worth is derived.

```text
Net Worth = Total Assets - Total Liabilities
```

Assets may include:

```text
Bank balances
Cash
Wallet balances
Investments
```

Liabilities may include:

```text
Credit card debt
Loans
Other liabilities
```

Do not store net worth as the primary source of truth.

Historical net-worth snapshots may be introduced later.

---

# 37. Notifications

## Table

```text
notifications
```

### Fields

```text
id                  UUID PK
user_id             UUID FK

notification_type   VARCHAR
title               VARCHAR
message             TEXT

entity_type         VARCHAR NULL
entity_id           UUID NULL

is_read             BOOLEAN
read_at             TIMESTAMPTZ NULL

created_at          TIMESTAMPTZ
```

### Notification Types

Examples:

```text
BUDGET_WARNING
BUDGET_EXCEEDED
GOAL_MILESTONE
GOAL_COMPLETED
BILL_REMINDER
MONTHLY_REPORT
FINANCIAL_INSIGHT
```

---

# 38. Notification Preferences

## Table

```text
notification_preferences
```

### Fields

```text
id                          UUID PK
user_id                     UUID FK

budget_alerts_enabled       BOOLEAN
goal_alerts_enabled         BOOLEAN
bill_reminders_enabled      BOOLEAN
monthly_report_enabled      BOOLEAN
news_notifications_enabled  BOOLEAN

created_at                  TIMESTAMPTZ
updated_at                  TIMESTAMPTZ
```

---

# 39. Financial Reports

## Table

```text
financial_reports
```

Purpose:

Stores generated report metadata.

### Fields

```text
id                  UUID PK
user_id             UUID FK

report_type         VARCHAR
period_start        DATE
period_end          DATE

status              VARCHAR

file_url             VARCHAR NULL
storage_key          VARCHAR NULL

generated_at        TIMESTAMPTZ NULL

created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

### Report Status

```text
PENDING
PROCESSING
COMPLETED
FAILED
```

The PDF itself should generally live in object storage rather than PostgreSQL.

---

# 40. News Sources

## Table

```text
news_sources
```

### Fields

```text
id                  UUID PK
name                VARCHAR
website_url         VARCHAR
is_active            BOOLEAN
created_at           TIMESTAMPTZ
updated_at           TIMESTAMPTZ
```

---

# 41. News Articles

## Table

```text
news_articles
```

### Fields

```text
id                  UUID PK
source_id           UUID FK

external_id         VARCHAR NULL

title               VARCHAR
summary             TEXT NULL

article_url         VARCHAR

published_at        TIMESTAMPTZ

image_url           VARCHAR NULL

is_featured         BOOLEAN
is_active            BOOLEAN

created_at          TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

---

# 42. News Tags

## Table

```text
news_tags
```

### Fields

```text
id                  UUID PK
name                VARCHAR UNIQUE
created_at          TIMESTAMPTZ
```

Example:

```text
Personal Finance
RBI
Markets
Tax
Mutual Funds
Investments
Economy
Insurance
```

---

# 43. News Article Tags

Many-to-many relationship:

```text
news_articles
        │
        │
        ▼
news_article_tags
        ▲
        │
news_tags
```

### Fields

```text
article_id          UUID FK
tag_id              UUID FK
```

Primary key:

```text
(article_id, tag_id)
```

---

# 44. Audit Logs

## Table

```text
audit_logs
```

Purpose:

Tracks important system mutations.

### Fields

```text
id                  UUID PK

user_id             UUID FK NULL

action              VARCHAR
entity_type         VARCHAR
entity_id           UUID NULL

old_values          JSONB NULL
new_values          JSONB NULL

request_id           VARCHAR NULL

created_at           TIMESTAMPTZ
```

### Examples

```text
TRANSACTION_CREATED
TRANSACTION_UPDATED
TRANSACTION_ARCHIVED

GOAL_CREATED
GOAL_CONTRIBUTION_ADDED

ACCOUNT_CREATED
ACCOUNT_ARCHIVED

IMPORT_STARTED
IMPORT_COMPLETED
```

Sensitive information should not be unnecessarily duplicated into audit logs.

---

# 45. Foreign Key Rules

Foreign keys should generally enforce ownership relationships.

Example:

```text
transactions.account_id
        ↓
accounts.id
```

But the backend must additionally verify:

```text
transaction.user_id == account.user_id
```

A foreign key alone does not guarantee cross-user ownership.

---

# 46. Delete Strategy

Financial records should generally not be hard-deleted.

Prefer:

```text
archived_at
deleted_at
is_deleted
```

depending on the entity.

For example:

```text
Transaction
    ↓
Archive
```

rather than permanently deleting financial history.

Hard deletion should be reserved for cases where:

- The record is invalid
- Legal/privacy requirements require deletion
- The entity has no financial history implications

---

# 47. Referential Delete Behavior

Recommended strategy:

## User

Deleting a user should eventually cascade or anonymize associated non-required data according to the application's data-retention policy.

## Account

Do not cascade-delete transactions.

Instead:

```text
Account → Archived
Transactions → Preserved
```

## Goal

Do not cascade-delete contributions.

Archive the goal while preserving its financial history.

## Category

Do not delete categories that are referenced by transactions.

Archive them.

---

# 48. Monetary Data Types

All monetary fields should use:

```text
NUMERIC(19,4)
```

or an appropriate precision based on the domain.

Python:

```text
Decimal
```

Avoid:

```text
float
```

for financial calculations.

---

# 49. Investment Quantity Precision

Investment quantities may require greater precision.

Recommended:

```text
NUMERIC(24,8)
```

Examples:

- Mutual fund units
- Fractional shares
- Gold quantity

The exact precision may be adjusted based on supported assets.

---

# 50. Currency

MoneyScope V1 primarily targets INR.

Currency should still be stored as an explicit field.

Example:

```text
currency = "INR"
```

Future multi-currency support should not require rebuilding the entire financial model.

---

# 51. Timezone

User timezone should be stored in:

```text
user_profiles.timezone
```

Default for the initial target market:

```text
Asia/Kolkata
```

The database should store timestamps using:

```text
TIMESTAMPTZ
```

---

# 52. Indexing Strategy

Indexes should be based on actual query patterns.

Important indexes include:

## Users

```text
users.email
```

---

## Accounts

```text
accounts.user_id
accounts.user_id, accounts.is_active
```

---

## Transactions

```text
transactions.user_id
transactions.user_id, transactions.occurred_at
transactions.user_id, transactions.category_id
transactions.user_id, transactions.account_id
transactions.user_id, transactions.payment_provider
transactions.user_id, transactions.transaction_type
transactions.user_id, transactions.source
```

For search:

```text
merchant_name
```

may eventually use PostgreSQL full-text or trigram indexes depending on requirements.

---

# 53. Transaction Date Index

A critical query pattern is:

```text
Get user's transactions for date range
```

Therefore:

```text
(user_id, occurred_at DESC)
```

should be a major index.

This supports:

- Dashboard recent transactions
- Monthly reports
- Analytics
- Date filters

---

# 54. Composite Index Strategy

Avoid creating an index for every column.

Indexes should be created around actual query patterns.

Example:

```text
(user_id, occurred_at DESC)
```

is generally more useful than independent indexes on:

```text
user_id
occurred_at
```

for user-specific date queries.

---

# 55. Unique Constraints

Important uniqueness rules:

```text
users.email UNIQUE
user_profiles.user_id UNIQUE
user_preferences.user_id UNIQUE
notification_preferences.user_id UNIQUE
budget_categories(budget_id, category_id) UNIQUE
investment_snapshots(user_id, snapshot_date) UNIQUE
news_article_tags(article_id, tag_id) PRIMARY KEY
```

External transaction references should use scoped uniqueness where reliable.

---

# 56. Check Constraints

Database-level checks should protect basic financial integrity.

Examples:

```text
amount > 0
target_amount > 0
budget.amount > 0
investment.invested_amount >= 0
investment.current_value >= 0
```

Do not rely entirely on API validation.

---

# 57. Enum Strategy

Database enums can be useful for stable values.

However, because financial product categories may evolve, simple string/VARCHAR values with application-level enums may be preferable for some domains.

Recommended approach:

## Stable Security/Status Values

Use application enums with strict validation.

## Frequently Evolving Product Values

Use lookup/reference tables or validated strings.

Avoid creating a PostgreSQL ENUM for every possible business concept.

---

# 58. JSONB Usage

JSONB should be used only for flexible or unstructured data.

Good examples:

```text
transaction_import_rows.raw_data
transaction_import_jobs.error_summary
audit_logs.old_values
audit_logs.new_values
```

Do not store core financial data as JSONB.

Bad:

```text
transactions.data JSONB
```

Core fields should remain relational and strongly typed.

---

# 59. Derived Data

The following should generally be derived rather than treated as the source of truth:

```text
Monthly Expense
Monthly Income
Savings
Savings Rate
Budget Utilization
Goal Progress
Net Worth
Portfolio Return
Financial Health
Safe-to-Spend
```

Example:

```text
Transactions
     ↓
Aggregation
     ↓
Monthly Expense
```

---

# 60. Cached Data

For performance, some derived data may later be cached.

Possible cached values:

```text
Dashboard summary
Analytics results
Financial health
Safe-to-spend
Portfolio summary
```

Cache invalidation must occur after relevant financial mutations.

The cache must never replace PostgreSQL as the authoritative source.

---

# 61. Dashboard Data Dependencies

Dashboard metrics depend on:

```text
Transactions
Accounts
Budgets
Goals
Investments
Liabilities
Notifications
```

Therefore dashboard queries should use efficient aggregation queries rather than loading all records into Python.

---

# 62. Analytics Query Strategy

For V1:

Use PostgreSQL aggregation.

Examples:

```text
SUM()
COUNT()
GROUP BY
DATE_TRUNC()
FILTER
```

Avoid:

```text
Load 100,000 transactions
        ↓
Python loop
        ↓
Calculate totals
```

Prefer:

```text
PostgreSQL
        ↓
Aggregation
        ↓
Small result set
        ↓
FastAPI
```

---

# 63. Database Transactions

Multi-step operations must be atomic.

Example:

## Goal Contribution

```text
BEGIN

Validate goal

Create contribution

Update cached goal balance if used

Create audit event

COMMIT
```

If any operation fails:

```text
ROLLBACK
```

---

# 64. Concurrency Control

Potential concurrent operations include:

- Goal contributions
- Account balance updates
- Transaction imports
- Budget updates
- Investment updates

Use:

- PostgreSQL transactions
- Appropriate row-level locking
- Unique constraints
- Idempotency keys where appropriate

Do not attempt to solve financial concurrency using frontend state.

---

# 65. Import Deduplication

CSV imports may contain duplicate transactions.

Possible duplicate signals:

```text
account_id
source
external_reference
occurred_at
amount
merchant
```

The exact duplicate detection algorithm belongs in the transaction import service.

Database constraints should provide the final safety boundary where a reliable unique identifier exists.

---

# 66. Data Ownership Model

Every user-owned financial table should include:

```text
user_id
```

Examples:

```text
accounts.user_id
transactions.user_id
budgets.user_id
goals.user_id
investment_holdings.user_id
liabilities.user_id
notifications.user_id
```

This makes authorization and user-scoped queries explicit.

---

# 67. Cross-User Data Protection

Every API query must follow the pattern:

```text
WHERE user_id = authenticated_user_id
```

Never:

```text
SELECT * FROM transactions
WHERE id = transaction_id
```

without ownership verification.

---

# 68. Database Migration Strategy

Alembic manages all schema changes.

Migration flow:

```text
Model Change
     ↓
Alembic Revision
     ↓
Review Migration
     ↓
Test Migration
     ↓
Apply to Development
     ↓
Apply to Staging
     ↓
Apply to Production
```

Never manually modify production schema without a corresponding migration.

---

# 69. Migration Rules

Every migration should be:

- Reviewable
- Reproducible
- Tested
- Small where practical

Avoid combining unrelated schema changes into one migration.

Before destructive migrations:

- Backup data
- Test migration
- Confirm rollback strategy

---

# 70. Seed Data

System-level seed data may include:

### Expense Categories

```text
Food
Groceries
Shopping
Travel
Transport
Bills
Entertainment
Healthcare
Education
Personal Care
Subscriptions
Rent
EMI
Insurance
Other
```

### Income Categories

```text
Salary
Freelance
Business
Interest
Dividend
Cashback
Refund
Bonus
Other
```

Seed data should be deterministic and safe to run in development/staging.

---

# 71. Database Backup Strategy

Production PostgreSQL must have automated backups.

Recommended:

- Automated daily backups
- Point-in-time recovery where supported
- Backup retention policy
- Periodic restore testing

A backup is not considered reliable until restoration has been tested.

---

# 72. Database Security

Production database should:

- Require authentication
- Use encrypted connections
- Restrict network access
- Use least-privilege credentials
- Never be publicly exposed unnecessarily
- Use separate development/staging/production credentials

---

# 73. Database Performance Strategy

Initial optimization order:

```text
Correct Schema
      ↓
Correct Queries
      ↓
Indexes
      ↓
Query Analysis
      ↓
Caching
      ↓
Read Replicas
```

Do not introduce advanced database infrastructure before measuring the actual bottleneck.

---

# 74. Future Scalability

The database should eventually support:

- Large transaction volumes
- Multiple accounts
- Multiple providers
- Multiple currencies
- Household scopes
- External financial integrations
- Historical financial snapshots

Potential future optimizations:

- Table partitioning for transactions
- Read replicas
- Materialized views
- Pre-aggregated analytics
- Data warehouse

These are not required for V1.

---

# 75. Recommended Initial Schema

The initial V1 schema is:

```text
users
user_profiles
user_preferences
refresh_tokens

accounts
linked_providers
liabilities

categories
merchants
transactions
transaction_import_jobs
transaction_import_rows

budgets
budget_categories

goals
goal_contributions

investment_holdings
investment_snapshots

notifications
notification_preferences

financial_reports

news_sources
news_articles
news_tags
news_article_tags

audit_logs
```

---

# 76. Domain Relationship Summary

```text
USER
 │
 ├── PROFILE
 ├── PREFERENCES
 ├── REFRESH TOKENS
 │
 ├── ACCOUNTS
 │      │
 │      └── TRANSACTIONS
 │              ├── CATEGORY
 │              └── MERCHANT
 │
 ├── BUDGETS
 │      └── BUDGET CATEGORIES
 │
 ├── GOALS
 │      └── GOAL CONTRIBUTIONS
 │
 ├── INVESTMENTS
 │      └── INVESTMENT SNAPSHOTS
 │
 ├── LIABILITIES
 │
 ├── NOTIFICATIONS
 │      └── NOTIFICATION PREFERENCES
 │
 ├── FINANCIAL REPORTS
 │
 └── AUDIT LOGS


NEWS SOURCE
    │
    ▼
NEWS ARTICLES
    │
    ▼
NEWS TAGS
```

---

# 77. Important Financial Rules

The following rules are mandatory.

## Rule 1

Money must use Decimal/fixed precision.

## Rule 2

Transfers are not expenses.

## Rule 3

Investment movements are not ordinary spending.

## Rule 4

Refunds must be represented explicitly.

## Rule 5

Financial records should not be casually hard-deleted.

## Rule 6

Every user-owned record must be scoped to its owner.

## Rule 7

Multi-step financial operations must be transactional.

## Rule 8

Derived financial metrics are not the primary source of truth.

## Rule 9

Database constraints must protect against invalid states.

## Rule 10

Frontend calculations must never be trusted as authoritative financial calculations.

---

# 78. Example — Expense

User spends ₹500 through PhonePe from HDFC.

```text
accounts
--------------------------------
HDFC Savings

transactions
--------------------------------
amount:              500.00
type:                EXPENSE
direction:           DEBIT
account:             HDFC Savings
payment_provider:    PhonePe
category:            Food
merchant:            Swiggy
source:              MANUAL
```

This contributes to:

- Monthly spending
- Food spending
- PhonePe spending
- HDFC account activity
- Budget utilization
- Financial health

---

# 79. Example — Bank Transfer

User moves ₹10,000 from HDFC to ICICI.

```text
Transaction A

amount: 10,000
type: TRANSFER
direction: DEBIT
account: HDFC


Transaction B

amount: 10,000
type: TRANSFER
direction: CREDIT
account: ICICI
```

This should not increase:

```text
Monthly Expenses
```

---

# 80. Example — Investment

User invests ₹5,000 into a mutual fund.

The transaction may be:

```text
type:
INVESTMENT

direction:
DEBIT

amount:
5,000
```

and the investment holding records:

```text
invested_amount:
5,000
```

The same money should not be counted as ordinary consumption.

---

# 81. Example — Refund

User receives ₹1,000 refund.

```text
type:
REFUND

direction:
CREDIT

amount:
1,000
```

The analytics layer should be able to distinguish refunds from ordinary income.

---

# 82. Example — Goal Contribution

User adds ₹2,000 toward an Emergency Fund.

```text
goal_contributions

amount:
2,000

goal:
Emergency Fund
```

If the contribution is linked to a financial transaction:

```text
source_transaction_id
```

can preserve the relationship.

---

# 83. Example — Monthly Analytics

For August:

```text
Income:
₹60,000

Expenses:
₹32,000

Investments:
₹8,000

Savings:
₹20,000
```

The analytics service should derive these from underlying financial records.

It should not depend on a manually updated:

```text
monthly_summary.total_expense
```

as the authoritative value.

---

# 84. Database Design Decisions

## Decision 1

PostgreSQL is the source of truth.

## Decision 2

UUIDs are used for primary identifiers.

## Decision 3

Money uses NUMERIC/Decimal.

## Decision 4

Transactions are the core financial event model.

## Decision 5

Accounts and payment providers are separate concepts.

## Decision 6

Transfers are not expenses.

## Decision 7

Derived metrics are calculated from source data.

## Decision 8

Important historical financial records are preserved.

## Decision 9

User ownership is explicit.

## Decision 10

Database constraints enforce critical integrity.

## Decision 11

Redis is only a cache/processing layer.

## Decision 12

Alembic controls schema evolution.

---

# 85. Database Design Boundary

This document defines:

```text
What data exists
How data relates
How data is protected
How financial data is represented
```

It does NOT define:

- FastAPI routes
- Pydantic request schemas
- Response schemas
- Authentication endpoints
- Service implementation
- Repository implementation

Those belong to:

`05_API_Contracts.md`

and

`06_Backend_Architecture.md`.

---

# 86. Final Database Architecture

MoneyScope's database follows:

```text
                  USERS
                    │
        ┌───────────┼────────────┐
        │           │            │
        ▼           ▼            ▼
    ACCOUNTS     GOALS       INVESTMENTS
        │           │            │
        ▼           ▼            ▼
 TRANSACTIONS  CONTRIBUTIONS  SNAPSHOTS
        │
   ┌────┼────┐
   ▼    ▼    ▼
CATEGORY MERCHANT PROVIDER
        │
        ▼
   ANALYTICS
        │
        ▼
 FINANCIAL HEALTH
        │
        ▼
     REPORTS
```

The database is designed around a simple principle:

> **Store reliable financial events and relationships; derive financial intelligence from them.**

This allows MoneyScope to evolve from a simple expense tracker into a broader financial platform without making the database dependent on any single frontend screen.

---

# Document Status

**Status:** Proposed for implementation

**Next Document:**

`05_API_Contracts.md`

The API contract should now be designed directly against this database model and the V1 feature freeze.