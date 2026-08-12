# 07_Development_Roadmap.md

# MoneyScope — Development Roadmap

> **Version:** 1.0.0
> **Status:** Development Roadmap
> **Frontend:** React 19 + TanStack Start + Vite + TypeScript
> **Backend:** FastAPI + Python
> **Database:** PostgreSQL
> **ORM:** SQLAlchemy 2.x
> **Migrations:** Alembic
> **Validation:** Pydantic v2
> **Authentication:** JWT
> **Testing:** Pytest
> **Architecture:** Modular Monolith

---

# 1. Purpose

This document converts the MoneyScope product and architecture documentation into an actionable development roadmap.

The purpose is to define:

- what to build
- in what order
- why that order matters
- what files should be created
- what should be tested
- what should be manually verified
- when frontend integration should happen
- what should not be built yet
- milestone completion criteria

The backend should **not** be implemented in one large operation.

Each milestone should produce a working and testable increment.

---

# 2. Development Philosophy

MoneyScope should be developed using:

```text
Plan
  ↓
Implement
  ↓
Test
  ↓
Verify
  ↓
Integrate
  ↓
Commit
  ↓
Next milestone
```

Do not follow:

```text
Generate entire backend
        ↓
Hope everything works
        ↓
Debug 200 files
```

---

# 3. Golden Rule

> **Never move to the next milestone until the current milestone is working and verified.**

Each milestone should have:

- implementation
- automated tests
- manual verification
- documentation update
- Git commit

---

# 4. Current Project State

The frontend already exists.

Current frontend:

```text
React 19
TanStack Start
TanStack Router
TypeScript
Vite
Tailwind CSS
Recharts
shadcn-style UI
```

The frontend currently uses mock financial data.

Primary mock source:

```text
frontend/src/lib/finance-data.ts
```

Existing routes include:

```text
/
 /analytics
 /transactions
 /goals
 /investments
 /news
 /settings
```

The frontend should be preserved while the backend is developed.

---

# 5. Target Architecture

Final initial architecture:

```text
                    MoneyScope PWA
                         │
                         │ HTTPS
                         ▼
                    FastAPI API
                         │
              ┌──────────┴──────────┐
              │                     │
         Business Logic        Authentication
              │
         Service Layer
              │
         Repository Layer
              │
          SQLAlchemy
              │
         PostgreSQL
```

Optional infrastructure:

```text
Redis
  │
  ▼
Background Worker
```

---

# 6. Overall Development Phases

```text
PHASE 0
Project Preparation

PHASE 1
Backend Foundation

PHASE 2
Authentication

PHASE 3
Finance Core

PHASE 4
Transaction Import

PHASE 5
Budgeting

PHASE 6
Dashboard

PHASE 7
Analytics

PHASE 8
Goals

PHASE 9
Investments

PHASE 10
Reports & Notifications

PHASE 11
News

PHASE 12
Frontend Integration

PHASE 13
Testing & Hardening

PHASE 14
PWA Production

PHASE 15
Future Intelligence
```

---

# 7. Phase 0 — Project Preparation

## Objective

Prepare the repository before writing backend business logic.

---

## Tasks

Create:

```text
backend/
docs/
```

Recommended structure:

```text
expense-tracker/
│
├── frontend/
│
├── backend/
│
└── docs/
```

If the current frontend is at the repository root, it may remain there initially.

Do not perform a large frontend restructuring merely for cosmetic reasons.

---

## Verify

Check:

```text
node -v
npm -v
python --version
```

Verify PostgreSQL availability.

Verify Git status.

Verify frontend still starts.

---

## Completion Criteria

```text
Frontend runs
Backend directory exists
Python environment ready
PostgreSQL available
Git clean / understood
```

---

# 8. Phase 1 — Backend Foundation

## Objective

Create a minimal production-quality FastAPI application.

---

## Build

Create:

```text
backend/
├── app/
│   ├── main.py
│   ├── core/
│   └── api/
│
├── tests/
├── alembic/
├── pyproject.toml
└── .env.example
```

---

## Install Core Dependencies

Expected core dependencies:

```text
fastapi
uvicorn
sqlalchemy
psycopg
alembic
pydantic
pydantic-settings
python-jose or equivalent JWT implementation
argon2-cffi
python-multipart
pytest
httpx
```

Additional dependencies should only be added when required.

---

## Implement

### FastAPI application

```text
GET /health
```

Expected:

```json
{
  "status": "ok"
}
```

---

## Configure

- environment variables
- CORS
- logging
- exception handling
- database configuration
- API versioning

---

## Verify

Run:

```text
uvicorn app.main:app --reload
```

Check:

```text
/health
/docs
/redoc
```

---

## Tests

At minimum:

```text
test_health()
test_application_startup()
```

---

## Milestone Completion

Do not continue until:

- FastAPI starts
- `/health` works
- OpenAPI works
- tests pass
- database connection configuration works

Git commit:

```text
chore: initialize fastapi backend
```

---

# 9. Phase 2 — Database Foundation

## Objective

Create the PostgreSQL foundation and migration system.

---

## Implement

SQLAlchemy:

```text
Base
Database session
Engine
Session dependency
```

Alembic:

```text
alembic init
```

Configure migrations.

---

## First Tables

Create foundational tables:

```text
users
user_profiles
```

Potential common fields:

```text
id
created_at
updated_at
```

---

## Database Rules

Use:

```text
UUID
TIMESTAMPTZ
NUMERIC
BOOLEAN
ENUM where appropriate
```

Avoid:

```text
FLOAT
```

for money.

---

## Verify

Run:

```text
alembic upgrade head
```

Verify tables in PostgreSQL.

---

## Tests

Verify:

```text
database connection
migration execution
rollback where practical
```

---

## Completion

Database migrations should work from a fresh database.

Git commit:

```text
feat: add database foundation
```

---

# 10. Phase 3 — Authentication

## Objective

Create secure user authentication.

---

## Implement

Tables:

```text
users
user_profiles
refresh_tokens
```

APIs:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

---

## Security

Use:

```text
Argon2 password hashing
JWT access tokens
Refresh tokens
```

Never store plain passwords.

---

## Implement Dependency

```text
get_current_user()
```

This becomes the foundation for all protected APIs.

---

## Tests

Test:

```text
register success
duplicate email
login success
invalid password
current user
invalid token
expired token
refresh token
logout
```

---

## Manual Verification

Use Swagger.

```text
Register
 ↓
Login
 ↓
Authorize
 ↓
GET /auth/me
```

---

## Completion

Authentication is considered complete when a protected endpoint can reliably identify the current user.

Git commit:

```text
feat: implement authentication
```

---

# 11. Phase 4 — Accounts

## Objective

Introduce financial accounts.

Examples:

```text
HDFC Savings
ICICI Savings
Cash
Credit Card
Wallet
```

---

## APIs

```text
GET    /accounts
POST   /accounts
GET    /accounts/{id}
PATCH  /accounts/{id}
DELETE /accounts/{id}
```

---

## Database

Create:

```text
accounts
```

---

## Rules

Every account belongs to one user.

Never allow:

```text
User A → User B account
```

---

## Tests

Test:

```text
create account
list accounts
update account
archive account
ownership isolation
```

---

# 12. Phase 5 — Categories

## Objective

Create standardized financial categories.

Initial categories:

```text
Food
Transport
Shopping
Bills
Entertainment
Health
Education
Travel
Investment
Other
```

---

## APIs

```text
GET    /categories
POST   /categories
PATCH  /categories/{id}
DELETE /categories/{id}
```

---

## Seed Data

Create system categories during development.

Example:

```text
Food
Transport
Shopping
Bills
```

---

## Important Rule

System categories should not be permanently deleted when historical transactions reference them.

---

# 13. Phase 6 — Transactions

## Objective

Build the most important MoneyScope domain.

This milestone is the **core of the entire application**.

---

# 14. Transaction Database

Create:

```text
transactions
```

Core fields:

```text
id
user_id
account_id
category_id
merchant_id / merchant_name
amount
transaction_type
direction
payment_provider
source
occurred_at
description
external_reference
created_at
updated_at
```

---

# 15. Transaction APIs

Implement:

```text
GET    /transactions
POST   /transactions
GET    /transactions/{id}
PATCH  /transactions/{id}
DELETE /transactions/{id}
```

---

# 16. Transaction Types

Initial types:

```text
INCOME
EXPENSE
TRANSFER
INVESTMENT
REFUND
```

---

# 17. Transaction Sources

Initial:

```text
MANUAL
CSV_IMPORT
```

Future:

```text
BANK_SYNC
UPI_SYNC
SMS
EMAIL
API
```

---

# 18. Payment Providers

Initial controlled values:

```text
PHONEPE
GOOGLE_PAY
PAYTM
BHIM
BANK_TRANSFER
CARD
CASH
OTHER
```

---

# 19. Transaction Business Rules

Examples:

```text
amount > 0
```

Expense:

```text
direction = DEBIT
```

Income:

```text
direction = CREDIT
```

Invalid combinations must be rejected.

---

# 20. Transaction Ownership

Every transaction must belong to the authenticated user.

The backend must verify:

```text
transaction.user_id == current_user.id
```

---

# 21. Transaction Concurrency

Financial operations must use database transactions.

Where required:

```text
SELECT ... FOR UPDATE
```

Use database constraints to prevent duplicate records.

---

# 22. Transaction Tests

At minimum:

```text
create expense
create income
update transaction
archive transaction
filter transactions
pagination
sorting
ownership isolation
invalid amount
invalid type
```

---

# 23. Critical Milestone

Before continuing, manually verify:

```text
User
 ↓
Account
 ↓
Category
 ↓
Transaction
```

Example:

```text
HDFC Account
      ↓
Food
      ↓
Swiggy
      ↓
₹450
      ↓
PhonePe
```

If this works correctly, the financial foundation exists.

Git commit:

```text
feat: implement transaction domain
```

---

# 24. Phase 7 — Transaction Import

## Objective

Allow the user to bring transactions from multiple UPI/bank sources.

This is critical because MoneyScope's main problem is:

> **"My transactions are spread across multiple apps."**

---

# 25. Import Architecture

```text
CSV Upload
    ↓
Import Job
    ↓
Background Worker
    ↓
Parse
    ↓
Validate
    ↓
Normalize
    ↓
Duplicate Detection
    ↓
Insert
```

---

# 26. Initial Import

Support:

```text
CSV
```

Do not initially build direct integrations for every UPI provider.

---

# 27. Import APIs

```text
POST /transactions/import
GET  /transactions/import/{job_id}
```

---

# 28. Duplicate Detection

Use:

```text
external_reference
```

where available.

Otherwise use a transaction fingerprint based on:

```text
account
amount
date
merchant
provider
```

---

# 29. Import Status

Possible:

```text
PENDING
PROCESSING
COMPLETED
FAILED
PARTIAL
```

---

# 30. Import Tests

Test:

```text
valid CSV
invalid CSV
missing columns
duplicate rows
large file
partial failure
retry
```

---

# 31. Phase 8 — Budgets

## Objective

Create spending controls.

---

## APIs

```text
GET /budgets
POST /budgets
PATCH /budgets/{id}
```

Category budgets:

```text
POST /budgets/{id}/categories
PATCH /budgets/{id}/categories/{category_id}
DELETE /budgets/{id}/categories/{category_id}
```

---

# 32. Budget Calculations

Backend calculates:

```text
budget
spent
remaining
utilization %
```

Example:

```text
Budget       ₹40,000
Spent        ₹32,000
Remaining     ₹8,000
Utilization      80%
```

---

# 33. Budget Tests

Test:

```text
create budget
category budget
spending aggregation
budget utilization
budget overrun
monthly boundary
```

---

# 34. Phase 9 — Dashboard Backend

## Objective

Replace frontend mock dashboard data with real backend data.

---

# 35. Dashboard APIs

```text
GET /dashboard/summary
GET /dashboard/trend
GET /dashboard/category-breakdown
GET /dashboard/recent-transactions
GET /dashboard/alerts
```

---

# 36. Dashboard Data

Dashboard should provide:

```text
today spent
monthly spent
monthly income
budget
remaining
safe-to-spend
savings
financial health
investment value
```

---

# 37. Dashboard Architecture

```text
Transactions
      │
      ├─────────┐
      ▼         ▼
   Budget    Analytics
      │         │
      └────┬────┘
           ▼
       Dashboard
```

---

# 38. Performance Rule

Do not make the dashboard load thousands of transactions and calculate everything in the frontend.

Use PostgreSQL aggregation.

---

# 39. Dashboard Tests

Verify:

```text
monthly totals
daily totals
category totals
recent transactions
budget summary
empty account
```

---

# 40. Phase 10 — Analytics

## Objective

Provide meaningful financial insights.

---

# 41. Analytics APIs

```text
GET /analytics/spending-overview
GET /analytics/categories
GET /analytics/payment-providers
GET /analytics/budget
GET /analytics/financial-health
GET /analytics/safe-to-spend
```

---

# 42. UPI Analytics

This is a major MoneyScope feature.

Example:

```text
PhonePe       ₹12,000
Google Pay     ₹9,000
Paytm          ₹4,000
----------------------
Total         ₹25,000
```

This answers:

> "How much did I actually spend through UPI?"

---

# 43. Monthly Spending

Analytics should show:

```text
Total spending
Average daily spending
Highest spending category
Highest spending day
UPI distribution
Budget utilization
Savings rate
```

---

# 44. Financial Health

Initial score factors:

```text
Savings Rate
Budget Control
Emergency Fund
Spending Stability
Investment Consistency
```

The algorithm should be versioned.

---

# 45. Safe-to-Spend

Calculate:

```text
Available money
- upcoming obligations
- goal commitments
- safety buffer
= safe-to-spend
```

The exact business formula must be documented before production use.

---

# 46. Analytics Tests

Test:

```text
monthly spending
category breakdown
UPI breakdown
budget utilization
savings rate
financial health
safe-to-spend
```

---

# 47. Phase 11 — Goals

## Objective

Help users turn savings into measurable financial targets.

Examples:

```text
Emergency Fund
Travel
New Laptop
Car
House
Education
```

---

# 48. Goal APIs

```text
GET    /goals
POST   /goals
GET    /goals/{id}
PATCH  /goals/{id}

POST   /goals/{id}/contributions
```

---

# 49. Goal Calculation

Example:

```text
Target:       ₹1,00,000
Saved:          ₹45,000
Remaining:      ₹55,000
Progress:           45%
```

---

# 50. Goal Contribution Atomicity

Adding money to a goal must be atomic.

```text
BEGIN
   ↓
Validate goal
   ↓
Create contribution
   ↓
Update goal state
   ↓
Audit
   ↓
COMMIT
```

---

# 51. Goal Tests

Test:

```text
create goal
update goal
contribution
progress calculation
overfunding
deadline
ownership
concurrent contributions
```

---

# 52. Phase 12 — Investments

## Objective

Track investments without requiring external broker integrations.

---

# 53. V1 Investment Strategy

Start with:

```text
Manual holdings
```

Examples:

```text
Mutual Funds
Stocks
FD
Gold
ETF
Crypto
Other
```

---

# 54. Investment APIs

```text
GET    /investments/portfolio
GET    /investments/holdings
POST   /investments/holdings
PATCH  /investments/holdings/{id}
DELETE /investments/holdings/{id}
```

---

# 55. Portfolio Metrics

Calculate:

```text
invested amount
current value
profit/loss
return %
allocation
portfolio trend
```

---

# 56. Future Investment Integration

Later:

```text
Market Data Provider
Broker Integration
Mutual Fund API
```

Do not block V1 on these.

---

# 57. Phase 13 — Notifications

## Objective

Create useful financial alerts.

Examples:

```text
Budget 80% used
Budget exceeded
Goal milestone reached
Unusual spending
Monthly report ready
```

---

# 58. Notification APIs

```text
GET /notifications
PATCH /notifications/{id}
POST /notifications/mark-all-read
```

---

# 59. Notification Architecture

```text
Transaction
    │
    ▼
Rules Engine
    │
    ▼
Notification
    │
    ▼
Frontend
```

---

# 60. Phase 14 — Monthly Reports

## Objective

Solve the month-end problem directly.

The user should be able to answer:

> **"Where did my money go this month?"**

---

# 61. Monthly Report

Include:

```text
Income
Expenses
Savings
Investments
Top categories
UPI provider breakdown
Budget utilization
Goal progress
Spending trends
```

---

# 62. Example

```text
August Financial Summary

Income              ₹60,000
Expenses            ₹32,000
Investments          ₹8,000
Savings             ₹20,000

Top Spending

Food                 ₹8,500
Shopping              ₹6,200
Transport             ₹4,500

UPI

PhonePe              ₹12,000
Google Pay             ₹9,000
Paytm                  ₹4,000
```

---

# 63. Phase 15 — News

## Objective

Add financial education and daily financial awareness.

---

# 64. News Features

Categories:

```text
Markets
RBI
Banking
Tax
Personal Finance
Investing
Economy
Technology
```

---

# 65. News Architecture

```text
News Provider
     ↓
Backend
     ↓
Cache
     ↓
MoneyScope API
     ↓
Frontend
```

Do not call third-party news APIs directly from the browser.

---

# 66. News Caching

News is read-heavy.

Potential strategy:

```text
External API
     ↓
Redis
     ↓
FastAPI
```

Refresh periodically.

---

# 67. Phase 16 — Frontend Integration

Only after the backend core is stable should the frontend progressively switch from mock data.

---

# 68. Integration Strategy

Do not remove all mock data at once.

Use:

```text
Mock
 ↓
API
```

route-by-route.

---

# 69. Integration Order

Recommended:

```text
1. Authentication
2. Transactions
3. Dashboard
4. Analytics
5. Budgets
6. Goals
7. Investments
8. Settings
9. Notifications
10. News
```

---

# 70. Frontend API Layer

Create:

```text
src/lib/api/
```

Example:

```text
client.ts
auth.ts
transactions.ts
dashboard.ts
analytics.ts
budgets.ts
goals.ts
investments.ts
settings.ts
news.ts
```

---

# 71. React Query

Use TanStack Query for server state.

Example conceptual flow:

```text
Route
 ↓
useQuery()
 ↓
API Client
 ↓
FastAPI
```

---

# 72. Query Keys

Use predictable query keys.

Example:

```text
["transactions"]
["transactions", filters]
["dashboard", month]
["analytics", period]
["goals"]
["investments"]
```

---

# 73. Cache Invalidation

After creating a transaction:

```text
transactions
dashboard
analytics
budget
financial-health
safe-to-spend
reports
```

should be considered stale.

---

# 74. Frontend Loading States

Every API-backed page must support:

```text
Loading
Success
Empty
Error
```

Example:

```text
Loading:
Skeleton

Empty:
"No transactions yet"

Error:
"Unable to load transactions"
```

---

# 75. Frontend Mock Removal

Once a route is fully connected:

Remove its dependency on:

```text
src/lib/finance-data.ts
```

Do not delete the entire file until every consumer has migrated.

---

# 76. Phase 17 — Testing & Hardening

After feature implementation, perform a dedicated hardening phase.

---

# 77. Backend Tests

Run:

```text
unit tests
integration tests
API tests
authentication tests
authorization tests
concurrency tests
```

---

# 78. Security Testing

Verify:

```text
User A cannot access User B data
Expired token rejected
Invalid refresh token rejected
Invalid input rejected
SQL injection impossible
Secrets not logged
CORS restricted
```

---

# 79. Financial Integrity Testing

Critical scenarios:

```text
duplicate transaction
duplicate contribution
concurrent contribution
transaction update
transaction archive
import duplicates
month boundary
timezone boundary
budget overrun
```

---

# 80. Performance Testing

Measure:

```text
Dashboard response
Transaction listing
Analytics queries
Monthly report
CSV import
```

Start with realistic data.

Example:

```text
10,000 transactions
100,000 transactions
```

---

# 81. Database Performance

Inspect:

```text
EXPLAIN ANALYZE
```

for heavy queries.

Optimize:

```text
indexes
joins
aggregations
pagination
```

before introducing complex infrastructure.

---

# 82. Phase 18 — PWA Production

Frontend should be prepared for production deployment.

Verify:

```text
PWA manifest
service worker
icons
installability
responsive layout
offline behavior
API connectivity
HTTPS
```

---

# 83. Production Architecture

Initial deployment:

```text
                 Internet
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
       Frontend             FastAPI
          │                   │
          │                   ▼
          │              PostgreSQL
          │
          └──── HTTPS ────────┘
```

Optional:

```text
Redis
Worker
```

---

# 84. Environment Strategy

Maintain:

```text
Development
Staging
Production
```

Never test destructive migrations directly on production.

---

# 85. CI/CD

Pipeline:

```text
Git Push
   ↓
Lint
   ↓
Type Check
   ↓
Unit Tests
   ↓
Integration Tests
   ↓
Build
   ↓
Migration Check
   ↓
Deploy
```

---

# 86. Git Strategy

Use small commits.

Examples:

```text
feat: initialize fastapi backend
feat: add database foundation
feat: implement authentication
feat: add accounts
feat: add categories
feat: implement transactions
feat: add csv transaction import
feat: add budgets
feat: add dashboard analytics
feat: add financial analytics
feat: add goals
feat: add investments
feat: add notifications
feat: add monthly reports
feat: integrate dashboard api
```

---

# 87. Branch Strategy

Recommended:

```text
main
  │
  ├── develop
  │
  ├── feature/backend-auth
  ├── feature/backend-transactions
  ├── feature/backend-analytics
  └── feature/frontend-api-integration
```

For a solo project, this can be simplified.

The important part is keeping changes isolated and reviewable.

---

# 88. Documentation Workflow

Before major implementation:

```text
Update docs
```

After implementation:

```text
Update docs if architecture changed
```

Documentation should never intentionally describe an architecture that the code does not follow.

---

# 89. Copilot Development Workflow

GitHub Copilot should work milestone-by-milestone.

Do not ask:

> "Build the entire MoneyScope backend."

Instead:

```text
Read docs/00 through docs/07.

Implement only Phase 1.

Do not implement future phases.

Show me the files you intend to create/change.

Wait for approval before making changes.
```

---

# 90. Copilot Modes

Recommended workflow:

### Plan Mode

Use when:

```text
Planning
Architecture
Database changes
Large feature
Refactoring
```

### Agent Mode

Use when:

```text
Implementation
Creating files
Running tests
Fixing errors
Making coordinated changes
```

### Ask Mode

Use when:

```text
Understanding code
Explaining errors
Reviewing architecture
Asking questions
```

---

# 91. Recommended Copilot Workflow

For every milestone:

```text
PLAN
 ↓
Review plan
 ↓
AGENT
 ↓
Implement
 ↓
Run tests
 ↓
ASK
 ↓
Review / understand
 ↓
Commit
```

---

# 92. Copilot Rule

Copilot must not make architectural decisions silently.

If it discovers a conflict with:

```text
00_Project_Context.md
01_Product_Vision.md
02_Feature_Freeze_V1.md
03_System_Architecture.md
04_Database_Design.md
05_API_Contracts.md
06_Backend_Architecture.md
```

it should stop and explain the conflict.

---

# 93. Milestone Verification Template

Every milestone should end with:

```text
## Implementation Summary

### Added
- ...

### Changed
- ...

### Tests
- ...

### Manual Verification
- ...

### Database Changes
- ...

### API Changes
- ...

### Known Issues
- ...

### Next Milestone
- ...
```

---

# 94. Definition of Done

A feature is not done merely because the code compiles.

A feature is complete when:

```text
Code
 +
Database
 +
API
 +
Validation
 +
Tests
 +
Error handling
 +
Authentication
 +
Authorization
 +
Documentation
```

are complete.

---

# 95. Critical Milestones

The project has several important checkpoints.

---

## Milestone A — Backend Foundation

```text
FastAPI
PostgreSQL
SQLAlchemy
Alembic
```

---

## Milestone B — Secure Backend

```text
Authentication
Authorization
User isolation
```

---

## Milestone C — Financial Core

```text
Accounts
Categories
Transactions
```

---

## Milestone D — Real Financial Visibility

```text
Transactions
+
Dashboard
+
Analytics
```

At this point the core product begins solving the original problem.

---

## Milestone E — Financial Planning

```text
Budgets
Goals
Safe-to-Spend
Financial Health
```

---

## Milestone F — Wealth Tracking

```text
Investments
Portfolio
Reports
```

---

## Milestone G — Product Intelligence

```text
News
Notifications
AI Insights
```

---

# 96. MVP Definition

The first meaningful MVP should be:

```text
Authentication
      +
Accounts
      +
Categories
      +
Transactions
      +
CSV Import
      +
Dashboard
      +
Analytics
      +
Budgets
      +
Goals
```

This is more valuable than rushing into AI.

---

# 97. MVP User Journey

A new user should be able to:

```text
Create Account
      ↓
Login
      ↓
Add Bank Account
      ↓
Add / Import Transactions
      ↓
Select Categories
      ↓
View Dashboard
      ↓
Understand Monthly Spending
      ↓
See UPI App Breakdown
      ↓
Create Budget
      ↓
Create Financial Goal
      ↓
Track Progress
```

---

# 98. Month-End User Journey

The most important product flow:

```text
End of Month
      ↓
Open MoneyScope
      ↓
Monthly Summary
      ↓
Income
      ↓
Expenses
      ↓
Savings
      ↓
Top Categories
      ↓
UPI Provider Breakdown
      ↓
Budget Performance
      ↓
Goal Progress
      ↓
Financial Health
      ↓
Next Month Recommendation
```

This should eventually become one of MoneyScope's strongest product experiences.

---

# 99. Daily User Journey

Daily experience:

```text
Open MoneyScope
      ↓
Today's Spending
      ↓
Safe-to-Spend
      ↓
Recent Transactions
      ↓
Budget Status
      ↓
Goal Progress
      ↓
Financial Alert
      ↓
Daily Financial News
```

---

# 100. Long-Term Product Evolution

After V1:

```text
V1
Financial Tracking
       ↓
V2
Financial Intelligence
       ↓
V3
Financial Automation
       ↓
V4
Personal Financial Assistant
```

---

# 101. V2 — Financial Intelligence

Potential features:

```text
Spending anomaly detection
Personalized insights
Monthly AI summary
Subscription detection
Recurring expense detection
Financial recommendations
Spending predictions
```

---

# 102. V3 — Financial Automation

Potential features:

```text
Automatic transaction categorization
Automatic recurring transaction detection
Bill reminders
Savings automation
Investment reminders
Smart budget recommendations
```

---

# 103. V4 — Personal Financial Assistant

Potential conversational queries:

```text
"How much did I spend on food this month?"

"Can I afford a ₹5,000 purchase?"

"Why did my spending increase this month?"

"How much should I save for my emergency fund?"

"Which UPI app did I use the most?"

"How much can I invest this month?"

"What changed in my finances this week?"
```

---

# 104. What NOT to Build Yet

Do not allow future ideas to interrupt the core roadmap.

Avoid implementing these before the MVP:

```text
AI chatbot
Direct UPI scraping
Bank integrations
Broker APIs
Complex investment automation
Microservices
Kubernetes
Real-time financial streaming
Advanced ML
Social features
Gamification
Multi-user households
```

Capture them in future planning instead.

---

# 105. Technical Debt Policy

Technical debt should be explicitly documented.

Use:

```text
docs/technical-debt.md
```

Each item:

```text
Problem
Impact
Temporary Solution
Recommended Solution
Priority
```

Do not silently accumulate architectural shortcuts.

---

# 106. Performance Principle

Optimize based on measurements.

Do not prematurely introduce:

```text
Redis
Kafka
Elasticsearch
Data Warehouse
Microservices
```

unless actual requirements justify them.

---

# 107. Scalability Principle

The modular monolith should be designed so individual domains can later be extracted.

For example:

```text
analytics/
```

could eventually become:

```text
analytics-service
```

without rewriting the entire application.

---

# 108. Product Priority

When deciding between features, use this priority:

```text
P0 — Financial correctness
P1 — Transaction visibility
P2 — Budgeting & goals
P3 — Analytics
P4 — Investments
P5 — Financial education
P6 — AI intelligence
P7 — Nice-to-have features
```

---

# 109. Core Product Metric

A useful north-star metric for MoneyScope:

> **How often can a user answer "Where did my money go?" without opening multiple financial apps?**

Supporting metrics may include:

```text
Transactions successfully imported
Monthly active users
Monthly reports viewed
Budget completion rate
Goal contribution frequency
Financial insights viewed
```

---

# 110. Final Development Sequence

The complete sequence is:

```text
00 Project Context
        ↓
01 Product Vision
        ↓
02 Feature Freeze
        ↓
03 System Architecture
        ↓
04 Database Design
        ↓
05 API Contracts
        ↓
06 Backend Architecture
        ↓
07 Development Roadmap
        │
        ▼
========================
 IMPLEMENTATION STARTS
========================
        │
        ▼
08 Backend Foundation
        ↓
09 Database Foundation
        ↓
10 Authentication
        ↓
11 Accounts
        ↓
12 Categories
        ↓
13 Transactions
        ↓
14 CSV Import
        ↓
15 Budgets
        ↓
16 Dashboard
        ↓
17 Analytics
        ↓
18 Goals
        ↓
19 Investments
        ↓
20 Notifications
        ↓
21 Reports
        ↓
22 News
        ↓
23 Frontend API Integration
        ↓
24 Testing & Hardening
        ↓
25 PWA Production
```

The numbered implementation documents after `07` are optional working documents; the seven core planning documents remain the source of truth.

---

# 111. First Coding Milestone

The **first actual coding task** after this documentation phase is:

> **Build only the FastAPI backend foundation.**

Do not start with transactions.

Do not start with authentication.

Do not create all database models.

First establish:

```text
backend/
├── app/
│   ├── main.py
│   ├── core/
│   └── api/
├── tests/
├── alembic/
├── pyproject.toml
└── .env.example
```

Then verify:

```text
FastAPI starts
        ↓
/health works
        ↓
/docs works
        ↓
PostgreSQL connection works
        ↓
Alembic works
        ↓
Tests pass
```

Only then proceed to authentication.

---

# 112. First Copilot Prompt

When you're ready to start coding, use **Copilot Plan Mode** first:

```text
Read these project documents completely before doing anything:

docs/00_Project_Context.md
docs/01_Product_Vision.md
docs/02_Feature_Freeze_V1.md
docs/03_System_Architecture.md
docs/04_Database_Design.md
docs/05_API_Contracts.md
docs/06_Backend_Architecture.md
docs/07_Development_Roadmap.md

Also inspect the existing frontend so you understand the current project structure.

We are now starting backend implementation.

For this task ONLY, plan Phase 1 — Backend Foundation from 07_Development_Roadmap.md.

Do NOT implement authentication, transactions, budgets, goals, investments, analytics, or other future modules yet.

I want you to:

1. Inspect the current repository structure.
2. Confirm where the FastAPI backend should live.
3. Propose the exact backend folder structure.
4. Identify required Python dependencies.
5. Define configuration/environment variables.
6. Define PostgreSQL connection setup.
7. Define SQLAlchemy 2.x setup.
8. Define Alembic setup.
9. Define FastAPI application setup.
10. Define CORS configuration.
11. Define centralized exception handling.
12. Define logging setup.
13. Define GET /health.
14. Define the initial test structure.
15. Explain every file you plan to create.
16. Explain any existing files you plan to modify.
17. Check for conflicts with the existing frontend architecture.

IMPORTANT:

- Do not change any files yet.
- Do not generate the implementation yet.
- Do not add unnecessary dependencies.
- Do not introduce microservices.
- Do not introduce Redis unless Phase 1 actually requires it.
- Do not modify the existing frontend unnecessarily.
- Follow docs/06_Backend_Architecture.md as the architectural source of truth.
- Follow docs/07_Development_Roadmap.md as the implementation sequence.

At the end, give me:

A. Proposed folder structure
B. Dependencies
C. Files to create
D. Files to modify
E. Implementation steps
F. Verification steps
G. Risks or decisions that need my approval

Wait for my approval before making changes.
```

### Then the workflow is simple:

**1. Plan Mode → review Copilot's plan**

**2. If plan looks correct → Agent Mode**

**3. Tell it:**

```text
Implement the approved Phase 1 plan exactly.

Do not implement anything outside Phase 1.

After implementation:
1. Run the backend tests.
2. Run lint/type checks if configured.
3. Start the FastAPI application.
4. Verify /health.
5. Verify /docs.
6. Verify PostgreSQL connectivity.
7. Verify Alembic migration setup.

Do not move to Phase 2.
```

**4. Then Ask Mode:**

```text
Review the Phase 1 implementation against
docs/06_Backend_Architecture.md and
docs/07_Development_Roadmap.md.

Do not modify anything.

Tell me:
- what is correct
- what is missing
- any architectural violations
- security issues
- unnecessary dependencies
- anything we should fix before starting Phase 2.
```

That gives us a **controlled engineering workflow** rather than letting Copilot turn the project into a 300-file spaghetti monster on day one. 😄