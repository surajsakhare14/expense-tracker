# 06_Backend_Architecture.md

# MoneyScope — Backend Architecture

> **Version:** 1.0.0
> **Status:** Architecture Definition
> **Backend:** FastAPI
> **Frontend:** React 19 + TanStack Start + Vite
> **Database:** PostgreSQL
> **ORM:** SQLAlchemy 2.x
> **Migrations:** Alembic
> **Validation:** Pydantic v2
> **Authentication:** JWT
> **Testing:** Pytest
> **API Style:** REST
> **API Version:** `/api/v1`

---

# 1. Purpose

This document defines the technical architecture of the MoneyScope backend.

The goal is to build a backend that is:

- production-ready
- maintainable
- modular
- testable
- secure
- scalable
- suitable for financial data
- easy to integrate with the existing frontend
- easy to extend with AI and financial intelligence later

The backend must not become a single large FastAPI application containing business logic inside route files.

---

# 2. Architecture Decision

MoneyScope will use a **modular layered architecture**.

```text
Frontend
   │
   │ HTTPS / REST
   ▼
FastAPI Routers
   │
   ▼
Service Layer
   │
   ▼
Repository Layer
   │
   ▼
SQLAlchemy ORM
   │
   ▼
PostgreSQL
```

Supporting infrastructure:

```text
                    ┌──────────────┐
                    │   FastAPI    │
                    └──────┬───────┘
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
          Auth          Finance       Analytics
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                      PostgreSQL
                           │
                    ┌──────┴──────┐
                    │             │
                    ▼             ▼
                 Redis        Background Jobs
```

---

# 3. Core Architectural Principle

The backend must separate:

### Transport

FastAPI routers handle:

- HTTP requests
- authentication dependencies
- request validation
- response serialization
- HTTP status codes

### Business Logic

Services handle:

- financial calculations
- transaction rules
- budget calculations
- goal calculations
- portfolio calculations
- financial health
- safe-to-spend

### Data Access

Repositories handle:

- SQLAlchemy queries
- database persistence
- filtering
- pagination
- database-specific operations

### Database

PostgreSQL handles:

- persistence
- constraints
- indexes
- transactions
- relational integrity

---

# 4. Request Flow

A typical request should flow like:

```text
Frontend
   │
   ▼
FastAPI Router
   │
   ├── Authentication
   │
   ├── Request Validation
   │
   ▼
Service
   │
   ├── Business Rules
   │
   ├── Authorization
   │
   ├── Calculations
   │
   ▼
Repository
   │
   ▼
SQLAlchemy
   │
   ▼
PostgreSQL
```

Example:

```text
POST /api/v1/transactions
        │
        ▼
transactions/router.py
        │
        ▼
TransactionService.create()
        │
        ├── validate account ownership
        ├── validate category
        ├── validate transaction type
        ├── check idempotency
        │
        ▼
TransactionRepository.create()
        │
        ▼
PostgreSQL
```

---

# 5. Recommended Project Structure

The backend should be created separately from the existing frontend.

Recommended repository structure:

```text
expense-tracker/
│
├── frontend/
│   └── existing TanStack Start application
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   ├── dependencies.py
│   │   │   ├── exceptions.py
│   │   │   └── logging.py
│   │   │
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── router.py
│   │   │       │
│   │   │       ├── auth/
│   │   │       ├── users/
│   │   │       ├── accounts/
│   │   │       ├── categories/
│   │   │       ├── transactions/
│   │   │       ├── budgets/
│   │   │       ├── goals/
│   │   │       ├── investments/
│   │   │       ├── dashboard/
│   │   │       ├── analytics/
│   │   │       ├── reports/
│   │   │       ├── notifications/
│   │   │       └── news/
│   │   │
│   │   ├── models/
│   │   │   ├── base.py
│   │   │   ├── user.py
│   │   │   ├── account.py
│   │   │   ├── transaction.py
│   │   │   ├── category.py
│   │   │   ├── budget.py
│   │   │   ├── goal.py
│   │   │   ├── investment.py
│   │   │   ├── notification.py
│   │   │   └── news.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── common.py
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── account.py
│   │   │   ├── transaction.py
│   │   │   ├── category.py
│   │   │   ├── budget.py
│   │   │   ├── goal.py
│   │   │   ├── investment.py
│   │   │   ├── dashboard.py
│   │   │   ├── analytics.py
│   │   │   └── news.py
│   │   │
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── transaction_service.py
│   │   │   ├── budget_service.py
│   │   │   ├── goal_service.py
│   │   │   ├── investment_service.py
│   │   │   ├── dashboard_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── financial_health_service.py
│   │   │   ├── safe_to_spend_service.py
│   │   │   └── report_service.py
│   │   │
│   │   ├── repositories/
│   │   │   ├── user_repository.py
│   │   │   ├── account_repository.py
│   │   │   ├── transaction_repository.py
│   │   │   ├── category_repository.py
│   │   │   ├── budget_repository.py
│   │   │   ├── goal_repository.py
│   │   │   ├── investment_repository.py
│   │   │   └── notification_repository.py
│   │   │
│   │   ├── integrations/
│   │   │   ├── news/
│   │   │   ├── market_data/
│   │   │   ├── payment_providers/
│   │   │   └── ai/
│   │   │
│   │   ├── workers/
│   │   │   ├── import_worker.py
│   │   │   ├── report_worker.py
│   │   │   └── notification_worker.py
│   │   │
│   │   └── utils/
│   │       ├── money.py
│   │       ├── dates.py
│   │       └── pagination.py
│   │
│   ├── migrations/
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── api/
│   │
│   ├── scripts/
│   │
│   ├── .env.example
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── README.md
│
└── docs/
```

---

# 6. Why Separate Frontend and Backend?

The frontend already exists as a polished TanStack Start application.

The backend should **not** be mixed into the frontend codebase.

Recommended:

```text
expense-tracker/
│
├── frontend/
│
├── backend/
│
└── docs/
```

Benefits:

- independent deployment
- independent scaling
- clean ownership
- easier testing
- easier CI/CD
- easier backend development
- FastAPI remains independent of TanStack Start
- future mobile apps can use the same API

The API should eventually support:

```text
Web PWA
   │
   ├── React/TanStack
   │
   ├── Mobile App
   │
   └── Future integrations
          │
          ▼
       FastAPI
```

---

# 7. FastAPI Application Entry Point

`app/main.py`

Responsibilities:

- create FastAPI application
- configure middleware
- configure CORS
- register API routers
- register exception handlers
- configure health endpoints
- initialize application-level resources

Conceptually:

```python
app = FastAPI(
    title="MoneyScope API",
    version="1.0.0",
)
```

Routers should not be defined directly inside `main.py`.

---

# 8. API Router Structure

Each domain owns its router.

Example:

```text
api/v1/transactions/
├── router.py
└── dependencies.py
```

Router responsibility:

```text
HTTP
 ↓
Validation
 ↓
Authentication
 ↓
Service
 ↓
Response
```

Router should **not** contain large business calculations.

Bad:

```python
@router.post("/")
def create_transaction(...):
    # 100 lines of business logic
```

Good:

```python
@router.post("/")
def create_transaction(...):
    return transaction_service.create(...)
```

---

# 9. Service Layer

The service layer contains business rules.

Example:

```text
services/
└── transaction_service.py
```

Responsibilities:

- validate business rules
- coordinate repositories
- manage transactions
- calculate derived values
- enforce domain policies

Example:

```python
class TransactionService:

    def create_transaction(
        self,
        user_id,
        payload,
    ):
        ...
```

---

# 10. Repository Layer

Repositories are responsible for persistence.

Example:

```text
repositories/
└── transaction_repository.py
```

Responsibilities:

- SQLAlchemy queries
- filtering
- pagination
- insert/update
- database-specific logic

Repository should not decide product business rules.

Bad:

```python
transaction_repository.create()
# calculate financial health
```

Good:

```text
Service
  ↓
Repository
  ↓
Database
```

---

# 11. SQLAlchemy

Use:

**SQLAlchemy 2.x**

Prefer modern typed SQLAlchemy models.

Example conceptual model:

```python
class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[UUID]
    user_id: Mapped[UUID]
    amount: Mapped[Decimal]
    occurred_at: Mapped[datetime]
```

Avoid legacy SQLAlchemy patterns where practical.

---

# 12. Database Sessions

Database sessions should be request-scoped.

Conceptually:

```text
HTTP Request
     │
     ▼
Create DB Session
     │
     ▼
Service
     │
     ▼
Repository
     │
     ▼
Commit / Rollback
     │
     ▼
Close Session
```

FastAPI dependency injection should provide the session.

---

# 13. Transaction Management

Financial mutations must use database transactions.

Example:

```text
BEGIN
   │
   ├── validate
   ├── create transaction
   ├── update related balance
   ├── create audit record
   │
COMMIT
```

If anything fails:

```text
ROLLBACK
```

Never leave partial financial state.

---

# 14. Financial Atomicity

For example:

```text
Create Expense
```

may involve:

```text
transactions
accounts
audit_events
```

These changes must be atomic.

```text
Transaction created
AND
Account balance updated
AND
Audit record created
```

must either all succeed or all fail.

---

# 15. Concurrency

Financial operations must assume concurrent requests.

Examples:

```text
Two requests adding money to same goal
Two transactions updating same account
Two imports processing same transaction
```

Use PostgreSQL transactions and appropriate locking where required.

Potential techniques:

- unique constraints
- row-level locks
- `SELECT ... FOR UPDATE`
- idempotency keys
- database transactions

---

# 16. Money Representation

Never use Python `float` for financial amounts.

Use:

```python
Decimal
```

Database:

```text
NUMERIC(18, 2)
```

Example:

```text
₹1250.50
```

should remain exact.

---

# 17. Financial Calculation Ownership

Calculations must happen on the backend.

Examples:

```text
monthly spending
budget utilization
safe-to-spend
savings rate
financial health
portfolio P/L
goal progress
monthly reports
```

The frontend should display backend results.

The frontend must not be the source of truth.

---

# 18. Pydantic Schemas

Use Pydantic v2 for:

- request validation
- response serialization
- API contracts

Separate request and response schemas.

Example:

```text
TransactionCreate
TransactionUpdate
TransactionResponse
TransactionListResponse
```

Do not use SQLAlchemy models directly as API contracts.

---

# 19. Example Schema Structure

```python
class TransactionCreate(BaseModel):
    account_id: UUID
    category_id: UUID
    merchant_name: str
    amount: Decimal
    transaction_type: TransactionType
    direction: TransactionDirection
    occurred_at: datetime
```

Response:

```python
class TransactionResponse(BaseModel):
    id: UUID
    amount: Decimal
    merchant_name: str
    occurred_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
```

---

# 20. Authentication Architecture

MoneyScope should use:

```text
JWT Access Token
+
Refresh Token
```

Flow:

```text
Login
  │
  ▼
FastAPI
  │
  ├── verify password
  │
  ▼
Access Token
Refresh Token
```

Frontend sends access token with API requests.

---

# 21. Password Security

Passwords must never be stored directly.

Use a secure password hashing algorithm such as:

```text
Argon2
```

or another approved modern password hashing implementation.

Never store:

```text
plain_password
```

---

# 22. Authentication Dependency

Protected routes should use a reusable dependency.

Conceptually:

```python
current_user = Depends(get_current_user)
```

Example:

```python
@router.get("/")
def get_transactions(
    current_user: User = Depends(get_current_user),
):
    ...
```

---

# 23. Authorization

Authentication answers:

> Who are you?

Authorization answers:

> Are you allowed to access this resource?

Every financial resource must be user-scoped.

Example:

```text
GET /goals/123
```

must verify:

```text
goal.user_id == current_user.id
```

---

# 24. Multi-User Isolation

Never trust:

```json
{
  "user_id": "..."
}
```

from the frontend.

The backend obtains user identity from the authenticated session/token.

This prevents:

```text
User A
   ↓
attempts to access
   ↓
User B's transaction
```

---

# 25. Domain Modules

The backend should be divided into business domains.

Core domains:

```text
Auth
Users
Accounts
Categories
Transactions
Budgets
Goals
Investments
Dashboard
Analytics
Notifications
Reports
News
```

Each domain should have clear responsibilities.

---

# 26. Transactions Domain

The transaction domain is the most important domain in MoneyScope.

Responsibilities:

- create transaction
- update transaction
- archive transaction
- search transactions
- filter transactions
- categorize transaction
- import transactions
- normalize transaction
- detect duplicates

Transaction data becomes the foundation for:

```text
Dashboard
Analytics
Budgets
Reports
Financial Health
Safe-to-Spend
AI Insights
```

---

# 27. Transaction Import Architecture

CSV import should not process huge files inside a normal request.

Preferred:

```text
Upload CSV
    │
    ▼
Create Import Job
    │
    ▼
202 Accepted
    │
    ▼
Background Worker
    │
    ├── parse
    ├── validate
    ├── normalize
    ├── detect duplicates
    └── insert
```

Frontend polls:

```text
GET /transactions/import/{job_id}
```

---

# 28. Transaction Normalization

Different UPI applications may represent transactions differently.

Example:

```text
PhonePe:
SWIGGY INDIA

Google Pay:
Swiggy Pvt Ltd

Paytm:
SWIGGY
```

Backend normalization can eventually produce:

```text
merchant_name = Swiggy
```

This is important for accurate analytics.

---

# 29. Provider Registry

Payment providers should use controlled values.

Examples:

```text
PHONEPE
GOOGLE_PAY
PAYTM
BHIM
BANK_TRANSFER
CASH
CARD
OTHER
```

Do not allow arbitrary provider names to become uncontrolled analytics dimensions.

---

# 30. Categories

Categories should support system and user-created categories.

Example:

```text
Food
Transport
Shopping
Bills
Entertainment
Health
Education
Investment
Travel
Other
```

System categories should not be permanently deleted if historical transactions reference them.

---

# 31. Budget Domain

Budget service handles:

- monthly budgets
- category budgets
- utilization
- remaining budget
- budget alerts

Example:

```text
Monthly Budget
       │
       ├── Food
       ├── Transport
       ├── Shopping
       └── Bills
```

---

# 32. Goal Domain

Goal service handles:

- financial targets
- contributions
- progress
- deadlines
- milestones

Example:

```text
Emergency Fund
Target: ₹1,00,000
Saved: ₹45,000
Progress: 45%
```

Goal contribution must be atomic.

---

# 33. Investment Domain

V1 investment tracking should initially support **manual portfolio tracking**.

Do not make live broker synchronization a V1 dependency.

Architecture should allow future providers:

```text
Investment Service
      │
      ├── Manual Provider
      │
      ├── Market Data Provider
      │
      └── Broker Provider
```

---

# 34. Investment Pricing

If live market data is added later:

```text
FastAPI
   │
   ▼
MarketDataService
   │
   ▼
External Provider
```

External credentials remain server-side.

Do not call financial providers directly from the browser.

---

# 35. Dashboard Domain

Dashboard is an aggregation layer.

It should not duplicate transaction business logic.

Example:

```text
DashboardService
      │
      ├── TransactionService / Repository
      ├── BudgetService
      ├── GoalService
      └── InvestmentService
```

Or, for performance-heavy aggregations:

```text
DashboardService
       ↓
Optimized SQL aggregation
```

---

# 36. Analytics Domain

Analytics is read-heavy.

Potential calculations:

```text
daily spending
monthly spending
category distribution
UPI provider distribution
budget utilization
savings rate
financial health
spending trends
```

Analytics should use database aggregations rather than loading every transaction into Python.

Bad:

```text
10 million transactions
        ↓
Python
        ↓
calculate totals
```

Better:

```text
PostgreSQL
   ↓
SUM()
GROUP BY
date_trunc()
   ↓
small result
   ↓
FastAPI
```

---

# 37. Analytics Performance

For V1:

- PostgreSQL aggregation
- proper indexes
- query optimization

Later:

- Redis caching
- materialized views
- pre-aggregated tables
- analytics warehouse if necessary

Do not introduce a data warehouse prematurely.

---

# 38. Safe-to-Spend Architecture

Safe-to-spend is a backend business calculation.

Conceptually:

```text
Available Funds
      │
      ├── Upcoming Bills
      ├── Goal Commitments
      ├── Budget Requirements
      └── Safety Buffer
              │
              ▼
        Safe-to-Spend
```

The calculation rules must be documented separately before production use.

The frontend only displays the result.

---

# 39. Financial Health Score

The financial health score should be implemented as a dedicated service.

Example factors:

```text
Savings Rate
Budget Control
Emergency Fund
Debt Load
Investment Consistency
Spending Stability
```

Architecture:

```text
FinancialHealthService
        │
        ├── savings score
        ├── budget score
        ├── emergency score
        └── investment score
                │
                ▼
             Score
```

The algorithm should be versioned.

Example:

```text
health_score_version = 1
```

This allows future algorithm changes without invalidating historical reports.

---

# 40. Reports

Reports may be expensive.

For simple reports:

```text
Request
 ↓
Generate
 ↓
Response
```

For large reports:

```text
Request
 ↓
Create Report Job
 ↓
202 Accepted
 ↓
Worker
 ↓
Generate
 ↓
Store
 ↓
Signed Download URL
```

---

# 41. Background Jobs

Background processing should be introduced for:

- CSV imports
- monthly report generation
- notification generation
- news ingestion
- market data synchronization
- future AI insight generation

Possible V1 technology:

```text
Redis
+
Celery / RQ / Arq
```

The exact worker technology can be finalized during implementation.

Do not add background infrastructure until the first asynchronous use case requires it.

---

# 42. News Architecture

News should be isolated from the core financial domain.

```text
News Router
    │
    ▼
News Service
    │
    ▼
News Provider
```

Potential providers:

```text
RSS
News API
Financial News Provider
Internal Curated Content
```

External API keys must remain backend-only.

---

# 43. AI Architecture

AI is a future capability.

Do not put AI logic directly inside transaction routes.

Preferred:

```text
Transaction Data
      │
      ▼
Analytics / Insights Service
      │
      ▼
AI Service
      │
      ▼
LLM Provider
```

AI can later generate:

- spending insights
- unusual spending alerts
- savings recommendations
- monthly summaries
- goal suggestions
- financial education

---

# 44. AI Safety Boundary

AI must not directly modify financial records.

For example:

```text
AI says:
"Reduce food spending by ₹2,000."
```

This becomes:

```text
Recommendation
```

not:

```text
Automatic financial action
```

The user remains in control.

---

# 45. Integrations

External integrations should live under:

```text
app/integrations/
```

Examples:

```text
integrations/
├── news/
├── market_data/
├── payment_providers/
└── ai/
```

Do not place provider-specific code inside generic services.

---

# 46. Dependency Injection

FastAPI dependency injection should provide:

- database session
- authenticated user
- configuration
- services where appropriate

Example conceptual flow:

```text
Router
  ↓
Depends(get_db)
Depends(get_current_user)
  ↓
Service
```

---

# 47. Configuration

Use environment variables.

Example:

```text
DATABASE_URL=
TEST_DATABASE_URL=
JWT_SECRET_KEY=
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=
JWT_REFRESH_TOKEN_EXPIRE_DAYS=

REDIS_URL=

CORS_ORIGINS=

NEWS_API_KEY=
MARKET_DATA_API_KEY=
AI_API_KEY=
```

Never commit secrets.

---

# 48. Environment Separation

Support:

```text
development
testing
staging
production
```

Example:

```text
.env
.env.example
.env.test
```

Production secrets must be managed through the deployment platform's secret manager/environment configuration.

Pytest must run with `ENVIRONMENT=testing` and an explicit `TEST_DATABASE_URL` targeting a dedicated PostgreSQL database named `moneyscope_test`. Test setup must reject missing, development, or unapproved targets before connecting, applying migrations, or writing data. `DATABASE_URL` remains the development/staging/production application and Alembic target outside test mode. Test data is isolated with per-test transaction rollback; pytest must not create, drop, truncate, or delete development data.

---

# 49. CORS

FastAPI should allow only configured frontend origins.

Development:

```text
http://localhost:3000
http://localhost:5173
```

Production:

```text
https://app.<domain>
```

Do not use:

```text
allow_origins=["*"]
```

in production.

---

# 50. Logging

Use structured application logging.

Important events:

```text
authentication failures
transaction creation
transaction import
financial mutation failures
external provider errors
background job failures
security-sensitive actions
```

Do not log:

```text
passwords
JWT tokens
API secrets
full sensitive financial payloads
```

---

# 51. Audit Logging

Financial systems benefit from audit records.

Potential events:

```text
TRANSACTION_CREATED
TRANSACTION_UPDATED
TRANSACTION_ARCHIVED

GOAL_CREATED
GOAL_CONTRIBUTION_CREATED

INVESTMENT_CREATED
INVESTMENT_UPDATED

ACCOUNT_CREATED
ACCOUNT_ARCHIVED
```

Audit logs should be append-oriented.

---

# 52. Database Indexing

Important indexes should include:

```text
transactions.user_id
transactions.occurred_at
transactions.account_id
transactions.category_id
transactions.payment_provider
transactions.user_id + occurred_at

goals.user_id
investments.user_id
budgets.user_id
```

Composite indexes should be added based on actual query patterns.

---

# 53. Database Constraints

Business-critical rules should be reinforced by the database.

Examples:

```text
amount > 0
target_amount > 0
unique(user_id, external_reference)
foreign keys
unique idempotency keys
```

Do not rely only on frontend validation.

---

# 54. Soft Delete

Financial records should generally use archival status rather than hard deletion.

Examples:

```text
Account
Category
Transaction
Investment Holding
Goal
```

Possible field:

```text
deleted_at
```

or:

```text
status = ARCHIVED
```

The exact approach should be standardized across the backend.

---

# 55. API Pagination

Repositories should provide reusable pagination utilities.

Example:

```text
PaginationParams
PaginationMeta
PaginatedResponse
```

Avoid rewriting pagination logic in every router.

---

# 56. Exception Handling

Create centralized exception handling.

Example:

```text
DomainException
ValidationException
ResourceNotFoundException
AuthorizationException
ConflictException
```

Map them to HTTP responses centrally.

Example:

```text
ResourceNotFoundException
        ↓
404
```

---

# 57. Service Exceptions

Services should raise domain-level exceptions.

Example:

```python
raise GoalNotFoundError()
```

rather than:

```python
raise HTTPException(status_code=404)
```

This keeps business logic independent of FastAPI.

---

# 58. Router Responsibility Rule

Routers should understand HTTP.

Services should understand business.

Repositories should understand database.

This rule should be enforced throughout the project.

```text
Router      → HTTP
Service     → Business
Repository  → Database
Model       → Persistence
Schema      → API Contract
```

---

# 59. Testing Architecture

Testing should have three levels.

```text
tests/
├── unit/
├── integration/
└── api/
```

---

# 60. Unit Tests

Test business logic without requiring the full API.

Examples:

```text
calculate_safe_to_spend()
calculate_goal_progress()
calculate_financial_health()
calculate_budget_utilization()
calculate_portfolio_return()
```

---

# 61. Integration Tests

Test:

```text
Service
+
Repository
+
PostgreSQL
```

Examples:

```text
create transaction
update transaction
goal contribution
budget calculation
transaction import
```

Use a dedicated test database.

Provision the local test database manually and use a least-privilege role restricted to it. Test setup may migrate the dedicated database to head only after verifying the connected database name is `moneyscope_test`.

---

# 62. API Tests

Test actual HTTP behavior.

Example:

```text
POST /api/v1/transactions
GET /api/v1/transactions
PATCH /api/v1/transactions/{id}
```

Verify:

- status code
- response shape
- validation
- authentication
- authorization

---

# 63. Authentication Tests

Must cover:

```text
valid login
invalid password
expired access token
invalid refresh token
missing token
accessing another user's resource
```

---

# 64. Financial Concurrency Tests

Important operations should have concurrency tests.

Examples:

```text
two simultaneous goal contributions
two simultaneous account updates
duplicate transaction submission
duplicate import processing
```

Expected result:

```text
Database remains consistent
```

---

# 65. Test Data

Use factories/fixtures rather than manually repeating large objects.

Example:

```text
UserFactory
AccountFactory
TransactionFactory
GoalFactory
InvestmentFactory
```

---

# 66. API Documentation

FastAPI's generated OpenAPI documentation should be maintained.

Development:

```text
/docs
```

and:

```text
/redoc
```

API descriptions should explain:

- purpose
- authentication
- request fields
- response fields
- error conditions

---

# 67. Health Checks

Backend should expose:

```http
GET /health
```

Example:

```json
{
  "status": "ok"
}
```

Optional readiness endpoint:

```http
GET /health/ready
```

which can verify:

```text
API
Database
Redis
```

---

# 68. Frontend Integration

The current frontend should continue using:

```text
TanStack Start
React Query
```

for server state.

Recommended frontend flow:

```text
TanStack Route
      │
      ▼
React Query
      │
      ▼
API Client
      │
      ▼
FastAPI
```

---

# 69. Frontend API Client

The frontend should have a centralized API client.

Example:

```text
frontend/src/lib/api/client.ts
```

Responsibilities:

- base URL
- authorization headers
- JSON parsing
- error normalization
- refresh token handling
- request IDs

Route components should not construct URLs manually.

---

# 70. API Types

Prefer generated TypeScript types from FastAPI OpenAPI once the backend stabilizes.

Potential flow:

```text
FastAPI
   ↓
OpenAPI
   ↓
Generated TypeScript Types
   ↓
Frontend
```

This minimizes frontend/backend contract mismatch.

---

# 71. PWA Considerations

The frontend is a PWA.

The backend must therefore support:

- HTTPS in production
- stable REST APIs
- token refresh
- retry-safe operations
- intermittent connectivity handling
- API timeouts

---

# 72. Offline Strategy

V1 should **not** attempt full offline financial synchronization.

Recommended V1:

```text
Offline
 ↓
Display cached read-only data
```

Mutations should require a reliable connection unless an offline queue is explicitly implemented later.

---

# 73. API Retry Strategy

GET requests may be safely retried.

Financial POST requests should not blindly retry.

Use:

```text
Idempotency-Key
```

for retry-sensitive mutations.

This is particularly important for:

```text
transactions
goal contributions
imports
```

---

# 74. Rate Limiting

Rate limits should eventually apply to:

```text
login
register
refresh
CSV import
report generation
AI endpoints
news ingestion
```

Normal read APIs can have higher limits.

---

# 75. Security Priorities

MoneyScope handles financial information.

Therefore priority order:

```text
1. Authentication
2. Authorization
3. Data isolation
4. Input validation
5. Database integrity
6. Secret management
7. Audit logging
8. Rate limiting
9. Monitoring
```

---

# 76. Deployment Architecture

Initial production architecture can remain simple.

```text
                 Internet
                    │
                    ▼
             Frontend / PWA
                    │
                    │ HTTPS
                    ▼
               FastAPI API
                    │
             ┌──────┴──────┐
             ▼             ▼
        PostgreSQL       Redis
```

Background workers:

```text
FastAPI
   │
   ▼
Redis / Queue
   │
   ▼
Worker
```

---

# 77. Deployment Principle

Do not over-engineer V1.

Avoid immediately introducing:

```text
Kubernetes
Microservices
Kafka
Separate analytics warehouse
Multiple databases
Complex service mesh
```

Start with a modular monolith.

---

# 78. Modular Monolith

MoneyScope backend should initially be:

```text
ONE FastAPI application
+
ONE PostgreSQL database
+
optional Redis
+
optional worker
```

But internally organized into domains.

```text
FastAPI
│
├── Auth
├── Transactions
├── Budgets
├── Goals
├── Investments
├── Analytics
└── Reports
```

This gives most benefits of clean architecture without microservice complexity.

---

# 79. Future Microservice Boundary

If MoneyScope grows significantly, possible future extraction:

```text
Core Finance Service
        │
        ├── Transactions
        ├── Accounts
        └── Budgets

Investment Service

Analytics Service

Notification Service

AI Insights Service
```

But this should happen only when justified by scale or team boundaries.

---

# 80. CI/CD

Backend CI should eventually run:

```text
lint
format check
type check
unit tests
integration tests
API tests
migration validation
```

Example pipeline:

```text
Push
 ↓
Install
 ↓
Lint
 ↓
Type Check
 ↓
Tests
 ↓
Build
 ↓
Deploy
```

---

# 81. Code Quality

Recommended tools:

```text
Ruff
Pytest
MyPy or Pyright
Black-compatible formatting through Ruff
Pre-commit
```

The exact tool combination can be finalized during implementation.

---

# 82. Type Safety

Use typing throughout the backend.

Prefer:

```python
def get_transaction(
    transaction_id: UUID,
) -> TransactionResponse:
    ...
```

Avoid excessive:

```python
Any
```

Especially in:

- services
- schemas
- repositories
- financial calculations

---

# 83. Domain Enums

Use controlled enums for important financial concepts.

Examples:

```text
TransactionType
TransactionDirection
AccountType
InvestmentAssetType
GoalStatus
BudgetPeriodType
PaymentProvider
TransactionSource
```

This prevents inconsistent values.

---

# 84. Timezone

The application is primarily intended for Indian users.

Default timezone:

```text
Asia/Kolkata
```

However, the backend should store timestamps in UTC where appropriate and convert them for user-facing calculations using the user's configured timezone.

This matters for:

```text
daily spending
month boundaries
monthly reports
notifications
```

---

# 85. Monthly Boundary

The backend must not assume:

```text
UTC month == user's month
```

For a user in India:

```text
2026-08-01 00:00 Asia/Kolkata
```

must be correctly converted before querying UTC timestamps.

This is particularly important for month-end reports.

---

# 86. Financial Data Lifecycle

A transaction should follow:

```text
Created
   ↓
Normalized
   ↓
Categorized
   ↓
Included in Analytics
   ↓
Included in Reports
```

If edited:

```text
Updated
   ↓
Dependent aggregates invalidated
```

---

# 87. Data Source Strategy

V1 should support:

```text
Manual Entry
CSV Import
```

Future:

```text
Bank Sync
UPI-related integrations
SMS parsing
Email parsing
Provider APIs
```

Do not design V1 around unofficial UPI scraping.

---

# 88. Multi-UPI Strategy

MoneyScope should treat:

```text
PhonePe
Google Pay
Paytm
BHIM
```

as **payment sources/providers**, not separate financial systems.

The financial truth remains:

```text
Transaction
+
Account
+
Amount
+
Category
+
Timestamp
+
Provider
```

This allows unified analytics.

---

# 89. Duplicate Detection

Duplicate detection is critical for imported transactions.

Potential matching fields:

```text
account
amount
occurred_at
merchant
reference_id
provider
```

A deterministic fingerprint may be generated.

Example conceptual:

```text
hash(
    account_id +
    amount +
    occurred_at +
    merchant +
    reference_id
)
```

The exact algorithm should be finalized during transaction-import implementation.

---

# 90. Auditability

Financial mutations should be traceable.

Example:

```text
User
 ↓
Transaction created
 ↓
Audit Event
```

Audit records should include:

```text
actor
action
resource
resource_id
timestamp
metadata
```

Avoid storing unnecessary sensitive data.

---

# 91. Database Migration Strategy

All schema changes must go through:

```text
Alembic
```

Never manually modify production schema.

Flow:

```text
SQLAlchemy Model
      ↓
Alembic Migration
      ↓
Review
      ↓
Test
      ↓
Production
```

---

# 92. Migration Rules

Every migration must be:

- reversible where practical
- tested
- reviewed
- small enough to understand

Avoid mixing unrelated schema changes in one migration.

---

# 93. Seed Data

Development environment may have seed data for:

```text
categories
demo user
demo transactions
demo goals
demo investments
```

Seed data must never accidentally run against production.

---

# 94. Development Workflow

Recommended workflow:

```text
1. Define requirement
       ↓
2. Update documentation
       ↓
3. Update database model
       ↓
4. Create Alembic migration
       ↓
5. Create Pydantic schemas
       ↓
6. Create repository
       ↓
7. Create service
       ↓
8. Create router
       ↓
9. Write tests
       ↓
10. Connect frontend
       ↓
11. Verify OpenAPI contract
```

---

# 95. Backend Implementation Order

The backend should be implemented in this order:

## Phase 1 — Foundation

```text
FastAPI setup
Configuration
PostgreSQL
SQLAlchemy
Alembic
Error handling
Logging
CORS
Health check
```

## Phase 2 — Authentication

```text
User
Registration
Login
JWT
Refresh token
Current user
```

## Phase 3 — Finance Core

```text
Accounts
Categories
Transactions
CSV import
```

## Phase 4 — Budgeting

```text
Budgets
Category budgets
Budget utilization
Alerts
```

## Phase 5 — Dashboard

```text
Dashboard summary
Recent transactions
Category breakdown
Trend
```

## Phase 6 — Analytics

```text
Spending analytics
UPI analytics
Financial health
Safe-to-spend
```

## Phase 7 — Goals

```text
Goals
Contributions
Progress
```

## Phase 8 — Investments

```text
Holdings
Portfolio
Allocation
P/L
```

## Phase 9 — Reports

```text
Monthly summary
Financial reports
```

## Phase 10 — News

```text
News ingestion
News API
Caching
```

---

# 96. V1 Backend Definition of Done

Backend V1 is considered functional when a user can:

```text
Register
   ↓
Login
   ↓
Create Account
   ↓
Create Categories
   ↓
Add Transactions
   ↓
Import Transactions
   ↓
View Unified Transactions
   ↓
View Dashboard
   ↓
View Monthly Analytics
   ↓
See UPI App Spending
   ↓
Create Budget
   ↓
Create Goal
   ↓
Track Goal Progress
   ↓
Track Investments
   ↓
View Financial Health
   ↓
View Safe-to-Spend
```

---

# 97. What V1 Does NOT Require

Do not block V1 on:

```text
Direct UPI API integration
Bank account synchronization
Broker synchronization
AI financial advisor
Advanced machine learning
Microservices
Kubernetes
Real-time market prices
Advanced tax planning
Automatic investment recommendations
```

These are future product phases.

---

# 98. Most Important Architectural Decision

The backend should be built as a:

> **Modular Monolith using FastAPI + SQLAlchemy + PostgreSQL.**

Not microservices.

Not a single giant `main.py`.

Not business logic inside routes.

Not frontend-driven calculations.

Architecture:

```text
             MoneyScope Backend
                    │
              FastAPI API
                    │
          ┌─────────┴─────────┐
          │                   │
      Domain Services     Authentication
          │
      Repositories
          │
      SQLAlchemy
          │
      PostgreSQL
```

---

# 99. Long-Term Product Architecture

The final product can eventually evolve toward:

```text
                         MoneyScope
                              │
                ┌─────────────┼─────────────┐
                │             │             │
             Finance       Insights      Education
                │             │             │
        ┌───────┼───────┐     │             │
        │       │       │     ▼             ▼
   Transactions Goals Investments      Financial News
        │       │       │
        └───────┼───────┘
                │
             Analytics
                │
                ▼
         Financial Intelligence
                │
        ┌───────┼────────┐
        ▼       ▼        ▼
     Budget  Health  Safe-to-Spend
```

The architecture defined in this document is intended to provide the foundation for that evolution.

---

# 100. Final Architecture Principles

MoneyScope backend must follow these principles:

1. **Modular monolith first.**
2. **FastAPI handles HTTP, not business logic.**
3. **Services own business rules.**
4. **Repositories own database access.**
5. **PostgreSQL is the financial source of truth.**
6. **Use SQLAlchemy 2.x.**
7. **Use Alembic for every schema change.**
8. **Use Pydantic v2 for API contracts.**
9. **Use Decimal for monetary values.**
10. **Use JWT-based authentication.**
11. **Every financial resource is user-scoped.**
12. **Financial mutations must be transactional.**
13. **Important mutations should support idempotency.**
14. **Analytics calculations belong on the backend.**
15. **UPI providers are transaction sources, not separate financial silos.**
16. **CSV import should be asynchronous when processing becomes expensive.**
17. **AI must remain isolated behind an Insights/AI service.**
18. **External provider credentials remain server-side.**
19. **Do not introduce microservices prematurely.**
20. **The API contract is the bridge between the existing frontend and FastAPI backend.**

---

## Next document

The natural next document is:

**`07_Development_Roadmap.md`**

That one should turn everything we've designed so far into an **actual implementation sequence**:

```text
Documentation
     ↓
Backend setup
     ↓
Database
     ↓
Auth
     ↓
Transactions
     ↓
Budgets
     ↓
Dashboard
     ↓
Analytics
     ↓
Goals
     ↓
Investments
     ↓
Frontend integration
     ↓
Testing
     ↓
PWA production
```

And importantly, we'll define **milestones + what Copilot should do at each milestone + what you should manually verify before moving to the next one**. That will keep us from letting Copilot generate a giant backend all at once.