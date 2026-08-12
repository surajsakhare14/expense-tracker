# 03_System_Architecture.md

# MoneyScope — System Architecture

> **Version:** 1.0.0
> **Status:** Architecture Definition
> **Product:** MoneyScope
> **Architecture Style:** API-First, Modular, Domain-Oriented
> **Primary Platform:** Progressive Web App (PWA)

---

# 1. Purpose

This document defines the high-level technical architecture of MoneyScope.

It describes:

- System components
- Frontend architecture
- Backend architecture
- API communication
- Database architecture
- Authentication
- Data flow
- Domain boundaries
- Caching
- Background processing
- File imports
- Notifications
- External integrations
- Security boundaries
- Deployment architecture
- Scalability strategy

This document does not define individual database tables or detailed API contracts.

Those will be defined separately in:

- `04_Database_Design.md`
- `05_API_Contracts.md`
- `06_Backend_Architecture.md`

---

# 2. Architectural Goals

MoneyScope architecture should provide:

## Maintainability

The system should be easy to understand and modify.

## Scalability

The architecture should support increasing users, transactions, and financial data without requiring a complete redesign.

## Security

Financial information must be isolated by user and protected throughout the system.

## Reliability

Financial operations must be transactional and consistent.

## Performance

Frequently accessed dashboards and analytics should not repeatedly execute expensive queries unnecessarily.

## Extensibility

Future integrations such as banks, UPI providers, investment platforms, and AI services should be possible without changing the core domain model.

## Testability

Business logic should be independently testable without requiring HTTP requests or a live frontend.

---

# 3. High-Level Architecture

MoneyScope follows an API-first architecture.

```text
                         ┌──────────────────────┐
                         │      User            │
                         │ Mobile / Desktop     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   MoneyScope PWA     │
                         │                      │
                         │ React 19             │
                         │ TanStack Start       │
                         │ TanStack Router      │
                         │ TanStack Query       │
                         │ TypeScript            │
                         └──────────┬───────────┘
                                    │
                              HTTPS / REST
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     FastAPI API      │
                         │                      │
                         │ Authentication       │
                         │ Domain APIs          │
                         │ Validation            │
                         │ Authorization         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Service Layer      │
                         │                      │
                         │ Business Rules       │
                         │ Financial Logic      │
                         │ Aggregations          │
                         └──────────┬───────────┘
                                    │
                         ┌──────────┴───────────┐
                         │                      │
                         ▼                      ▼
                ┌─────────────────┐    ┌─────────────────┐
                │ Repository/Data │    │ Background Jobs │
                │ Access Layer    │    │                 │
                └────────┬────────┘    └────────┬────────┘
                         │                      │
                         ▼                      ▼
                ┌─────────────────┐    ┌─────────────────┐
                │ PostgreSQL      │    │ Redis / Queue   │
                └─────────────────┘    └─────────────────┘
```

---

# 4. Technology Stack

## Frontend

The current Lovable-generated frontend is based on:

- React 19
- TanStack Start
- TanStack Router
- TanStack Query
- TypeScript
- Vite
- Tailwind CSS v4
- shadcn/ui
- Radix UI
- Recharts
- React Hook Form
- Zod
- Lucide Icons

The existing frontend should not be migrated to another framework for V1.

---

# 5. Backend

MoneyScope backend will use:

- Python
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Redis
- JWT-based authentication
- Pytest

FastAPI is responsible for:

- HTTP APIs
- Authentication
- Authorization
- Request validation
- Response serialization
- API documentation
- Dependency injection

FastAPI route handlers should remain thin.

Business logic belongs in the service layer.

---

# 6. Database

PostgreSQL is the primary system of record.

It stores:

- Users
- Accounts
- Transactions
- Categories
- Budgets
- Goals
- Investments
- Notifications
- Reports
- News metadata
- Audit information

Financial data must not rely on frontend state as the source of truth.

---

# 7. Source of Truth

The backend database is the authoritative source for financial data.

```text
Frontend
   │
   │ display / interaction
   ▼
FastAPI
   │
   │ business rules
   ▼
PostgreSQL
   │
   └── Source of Truth
```

The frontend may cache data for performance, but cached data must never become the authoritative financial record.

---

# 8. Frontend Architecture

The frontend is responsible for:

- Presentation
- Navigation
- User interaction
- Form handling
- Client-side validation
- API consumption
- Loading states
- Empty states
- Error states
- Local UI state
- Client-side caching

The frontend should not contain authoritative financial business logic.

---

# 9. Frontend Data Flow

The expected data flow is:

```text
User Action
    ↓
React Component
    ↓
TanStack Query / API Client
    ↓
FastAPI
    ↓
Service Layer
    ↓
Repository
    ↓
PostgreSQL
```

For reads:

```text
PostgreSQL
    ↓
Repository
    ↓
Service
    ↓
FastAPI Response
    ↓
TanStack Query
    ↓
React Component
```

---

# 10. TanStack Query

TanStack Query will be used as the primary frontend server-state management solution.

Responsibilities:

- API requests
- Caching
- Refetching
- Request deduplication
- Mutation state
- Loading state
- Error state
- Cache invalidation

Example conceptual query:

```text
useQuery({
    queryKey: ["transactions", filters],
    queryFn: fetchTransactions
})
```

The frontend should not manually duplicate server-state management across components.

---

# 11. API Communication

Frontend and backend communicate through REST APIs over HTTPS.

Example:

```text
GET /api/v1/transactions
POST /api/v1/transactions
PATCH /api/v1/transactions/{id}
DELETE /api/v1/transactions/{id}
```

All production APIs should be versioned.

Recommended prefix:

```text
/api/v1/
```

---

# 12. API Versioning

Versioning should be introduced from the beginning.

Example:

```text
/api/v1/auth
/api/v1/users
/api/v1/accounts
/api/v1/transactions
/api/v1/budgets
/api/v1/goals
/api/v1/investments
/api/v1/analytics
/api/v1/reports
/api/v1/notifications
/api/v1/news
```

Future breaking changes can use:

```text
/api/v2/
```

---

# 13. Domain Architecture

The backend is organized by business domains rather than frontend pages.

Core domains:

```text
Authentication
Users
Accounts
Categories
Transactions
Budgets
Goals
Investments
Analytics
Financial Health
Reports
Notifications
News
```

The domain dependency relationship is approximately:

```text
Authentication
      │
      ▼
Users
      │
      ▼
Accounts
      │
      ├───────────────┐
      ▼               ▼
Categories       Transactions
                      │
             ┌────────┼────────┐
             ▼        ▼        ▼
          Budgets    Goals   Investments
             │        │        │
             └────────┼────────┘
                      ▼
                  Analytics
                      │
                      ▼
               Financial Health
                      │
                      ▼
                   Reports
```

---

# 14. Transaction as a Core Domain

Transactions are one of the most important domains in MoneyScope.

Many other features depend on transactions:

```text
Transactions
    │
    ├── Dashboard
    ├── Analytics
    ├── Budgets
    ├── Reports
    ├── Financial Health
    └── Goals
```

Therefore transaction integrity is critical.

---

# 15. Account vs UPI Provider

MoneyScope must distinguish between:

## Account

Where the money actually exists.

Examples:

- HDFC Savings
- SBI Savings
- Cash
- Credit Card

## Payment Provider

How the transaction was initiated.

Examples:

- Google Pay
- PhonePe
- Paytm

Example:

```text
Account:
HDFC Savings

Payment Provider:
PhonePe

Merchant:
Swiggy

Amount:
₹450
```

This distinction is important for future bank and UPI integrations.

---

# 16. Transaction Types

MoneyScope must distinguish between different financial movements.

Initial types:

```text
EXPENSE
INCOME
TRANSFER
INVESTMENT
REFUND
```

Example:

```text
HDFC → ICICI

Type:
TRANSFER
```

This must NOT be treated as an expense.

Similarly:

```text
Bank → Mutual Fund

Type:
INVESTMENT
```

This should not automatically be treated as ordinary spending.

---

# 17. Financial Calculations

Financial calculations should primarily happen on the backend.

Examples:

- Monthly spending
- Monthly income
- Savings
- Savings rate
- Budget utilization
- Net worth
- Goal progress
- Portfolio value
- Financial health score
- Safe-to-spend

The frontend should display backend-derived values.

---

# 18. Money Representation

Financial amounts must not rely on floating-point arithmetic.

Avoid:

```python
float
```

for monetary calculations.

Use a fixed-precision decimal representation.

Recommended:

```text
PostgreSQL:
NUMERIC / DECIMAL

Python:
Decimal
```

Currency should be stored explicitly where appropriate.

Initial default:

```text
INR
```

---

# 19. Time and Date Handling

Financial systems are sensitive to dates.

The backend should:

- Store timestamps consistently
- Prefer UTC for persisted timestamps
- Store user timezone preference
- Convert dates for presentation
- Perform month/day calculations using the user's timezone

Example:

```text
Database:
UTC timestamp

User:
Asia/Kolkata

Frontend:
IST display
```

Month-based financial calculations must use the user's financial timezone rather than blindly using server time.

---

# 20. Authentication Architecture

Authentication uses:

```text
Email / Password
       ↓
FastAPI
       ↓
Password Verification
       ↓
Access Token + Refresh Token
```

Protected request:

```text
Frontend
   ↓
Authorization: Bearer <access_token>
   ↓
FastAPI
   ↓
Authenticate User
   ↓
Authorize Resource
   ↓
Service
```

---

# 21. Authorization

Every user-owned financial resource must be scoped to the authenticated user.

Example:

```text
User A

GET /api/v1/transactions/123
```

The backend must verify:

```text
transaction.user_id == authenticated_user.id
```

Never rely on the frontend to enforce ownership.

---

# 22. Multi-Tenancy

V1 uses a simple user-scoped model.

Conceptually:

```text
User
 ├── Accounts
 ├── Transactions
 ├── Goals
 ├── Budgets
 ├── Investments
 └── Reports
```

Every user must only be able to access their own financial records.

Future household/shared accounts can introduce an additional ownership/scope layer without redesigning the entire application.

---

# 23. Service Layer

Business logic belongs in services.

Example:

```text
transactions/router.py
        ↓
transactions/service.py
        ↓
transactions/repository.py
        ↓
PostgreSQL
```

The service layer handles:

- Business rules
- Financial calculations
- Transaction workflows
- Validation beyond schema validation
- Cross-domain operations
- Database transaction boundaries

---

# 24. Repository Layer

Repositories handle data access.

Example responsibilities:

```text
get_transaction()
list_transactions()
create_transaction()
update_transaction()
archive_transaction()
```

Repositories should not contain complex business rules.

---

# 25. Database Transaction Management

Financial mutations must use proper database transactions.

Example:

```text
Create Goal Contribution

BEGIN
   ↓
Validate Goal
   ↓
Create Contribution
   ↓
Update Goal Progress
   ↓
COMMIT
```

If any step fails:

```text
ROLLBACK
```

No partial financial state should be persisted.

---

# 26. Concurrency

Financial mutations must consider concurrent requests.

Examples:

- Two simultaneous goal contributions
- Two imports creating the same transaction
- Multiple updates to an account
- Concurrent balance calculations

Database constraints and transactional locking should be used where necessary.

The backend must not assume that frontend requests happen sequentially.

---

# 27. CSV Import Architecture

CSV imports should not block normal API requests for large files.

Initial flow:

```text
User
 ↓
Upload CSV
 ↓
FastAPI
 ↓
Validate File
 ↓
Create Import Job
 ↓
Redis / Background Worker
 ↓
Parse Rows
 ↓
Validate
 ↓
Detect Duplicates
 ↓
Persist Transactions
 ↓
Update Import Status
 ↓
Frontend Polls / Refreshes
```

Small imports may be processed synchronously initially, but the architecture should support background processing.

---

# 28. Redis

Redis is not the source of truth.

It is used for:

- Caching
- Background job queues
- Rate limiting
- Temporary processing state
- Frequently requested analytics

PostgreSQL remains authoritative.

---

# 29. Background Jobs

Background processing may be used for:

- CSV imports
- Monthly report generation
- Financial notifications
- News ingestion
- Scheduled reminders
- Analytics cache refresh
- Future AI insight generation

Initial architecture:

```text
FastAPI
   ↓
Redis Queue
   ↓
Worker
   ↓
PostgreSQL / External API
```

---

# 30. News Architecture

News should not be fetched from external providers on every user request.

Preferred architecture:

```text
External News Sources
        ↓
News Ingestion Job
        ↓
Normalize
        ↓
Store / Cache
        ↓
MoneyScope API
        ↓
Frontend
```

This provides:

- Better performance
- Reduced external API dependency
- Caching
- Consistent content
- Easier filtering

---

# 31. Investment Architecture

V1 investment tracking is primarily manual.

The system should support:

```text
User
 ↓
Investment Holding
 ↓
Invested Amount
 ↓
Current Value
 ↓
Profit/Loss
```

Future market data integration can update current values.

External market APIs must remain behind the backend.

Frontend must never directly expose provider API credentials.

---

# 32. Analytics Architecture

Analytics should use backend aggregation.

Example:

```text
Transactions
      ↓
Aggregation Query
      ↓
Analytics Service
      ↓
API Response
      ↓
TanStack Query
      ↓
Chart
```

For expensive analytics:

```text
Transactions
      ↓
Aggregation
      ↓
Cache
      ↓
Frontend
```

Analytics responses should support appropriate date ranges.

---

# 33. Dashboard Architecture

Dashboard is a consumer of multiple domains.

It should not own financial data.

```text
Accounts
Transactions
Budgets
Goals
Investments
Notifications
       │
       ▼
Dashboard Services
       │
       ▼
Dashboard API
       │
       ▼
Frontend
```

Dashboard endpoints may return pre-aggregated data to minimize multiple frontend requests.

However, composite endpoints should not create a giant monolithic backend service.

---

# 34. Safe-to-Spend Architecture

Safe-to-spend is a calculated estimate.

Potential inputs:

```text
Available Funds
+
Expected Income
-
Upcoming Bills
-
Budget Commitments
-
Savings Commitments
-
Goal Contributions
```

The calculation must be implemented as a dedicated backend service.

It should be:

- Deterministic
- Explainable
- Testable
- Versionable

The frontend should not implement the financial formula independently.

---

# 35. Financial Health Architecture

Financial health should be calculated by a dedicated domain/service.

Conceptually:

```text
Savings
Budget
Goals
Investments
Emergency Fund
Debt
Spending Behavior
        ↓
Financial Health Engine
        ↓
Score
        +
Explanation
        +
Recommendations
```

The scoring formula should be versioned.

Example:

```text
health_score_version = 1
```

This allows future changes without making historical reports impossible to understand.

---

# 36. Reports Architecture

Monthly reports may require expensive aggregation.

Preferred flow:

```text
User requests report
       ↓
FastAPI
       ↓
Report Service
       ↓
Analytics Aggregation
       ↓
Generate Report
       ↓
Store Report Metadata / File
       ↓
Return Report
```

Large PDF generation should eventually run as a background job.

---

# 37. Notifications Architecture

Notification events can be generated by business rules.

Example:

```text
Transaction
   ↓
Budget Calculation
   ↓
Budget > 80%
   ↓
Notification Event
   ↓
Notification Service
   ↓
Notification
```

Notification delivery channels may include:

- In-app
- Push
- Email

V1 should prioritize in-app notifications.

---

# 38. Error Handling

Backend errors should use consistent API responses.

Conceptually:

```json
{
  "error": {
    "code": "TRANSACTION_NOT_FOUND",
    "message": "Transaction could not be found.",
    "details": null,
    "request_id": "..."
  }
}
```

Frontend should use machine-readable error codes rather than parsing human-readable messages.

---

# 39. Validation

Validation occurs at multiple levels.

## Request Validation

Pydantic schemas.

Examples:

- Required fields
- String lengths
- Amount format
- Date format
- Enum values

## Business Validation

Service layer.

Examples:

- Account ownership
- Goal ownership
- Duplicate transaction
- Budget rules
- Investment constraints

## Database Validation

PostgreSQL.

Examples:

- Foreign keys
- Unique constraints
- Check constraints
- Not-null constraints

Validation should exist at the appropriate layer rather than relying on only one layer.

---

# 40. Logging

The backend should use structured logging.

Important events:

- Authentication failures
- API errors
- Import jobs
- Background job failures
- External API failures
- Security events

Logs must never contain:

- Passwords
- Access tokens
- Refresh tokens
- Sensitive financial data unnecessarily
- Secret API keys

---

# 41. Auditability

Financial mutations should be auditable.

Important operations include:

- Transaction creation
- Transaction modification
- Transaction deletion/archive
- Account changes
- Goal contributions
- Investment changes
- Import operations

V1 may begin with application-level timestamps and import history, while a full audit log can be expanded as the product matures.

---

# 42. Idempotency

Operations that can be retried should support idempotency where appropriate.

Important examples:

- CSV imports
- Payment/financial imports
- Future external synchronization
- Financial mutations triggered by retrying clients

A duplicate request should not accidentally create duplicate financial records.

---

# 43. API Rate Limiting

Rate limiting should protect:

- Authentication endpoints
- File upload endpoints
- Expensive analytics
- News endpoints
- Future AI endpoints

Redis can support distributed rate limiting.

---

# 44. File Storage

Files such as:

- CSV imports
- Generated PDF reports
- Future receipts

should not be stored permanently inside the application container.

Use object storage such as:

- Cloudflare R2
- AWS S3

The database should store metadata and references.

---

# 45. Secrets Management

Secrets must never be committed to Git.

Examples:

```text
DATABASE_URL
JWT_SECRET
REDIS_URL
NEWS_API_KEY
STORAGE_ACCESS_KEY
STORAGE_SECRET_KEY
```

Development:

```text
.env
```

Production:

Use the deployment provider's secure environment-variable system.

---

# 46. CORS

The backend must explicitly allow the production frontend origin.

Development may allow:

```text
http://localhost:3000
http://localhost:5173
```

Production origins must be explicitly configured.

Wildcard CORS should not be used for authenticated production APIs.

---

# 47. HTTPS

Production traffic must use HTTPS.

```text
Browser
   ↓
HTTPS
   ↓
Frontend
   ↓
HTTPS
   ↓
FastAPI
```

No financial API should be exposed over plain HTTP in production.

---

# 48. API Documentation

FastAPI automatically provides OpenAPI documentation.

Development endpoints:

```text
/docs
/redoc
```

Production exposure should be evaluated based on security and deployment requirements.

The API contract in `05_API_Contracts.md` remains the product-level API reference.

---

# 49. Testing Architecture

Testing should exist at multiple levels.

## Unit Tests

Test:

- Financial calculations
- Budget calculations
- Goal progress
- Safe-to-spend
- Financial health
- Validation rules

## Integration Tests

Test:

- API + database
- Authentication
- Transactions
- Imports
- Goals
- Accounts

## API Tests

Test:

- Status codes
- Request validation
- Response schemas
- Authorization

## Frontend Tests

Test:

- Components
- Forms
- User interactions
- API states

## End-to-End Tests

Critical workflows:

```text
Register
 ↓
Login
 ↓
Create Account
 ↓
Create Transaction
 ↓
View Dashboard
 ↓
Create Goal
 ↓
View Analytics
```

---

# 50. Deployment Architecture

Initial deployment:

```text
                         Internet
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
       ┌─────────────┐             ┌─────────────┐
       │   Vercel    │             │  FastAPI    │
       │  Frontend   │ ── HTTPS ──▶│   Backend   │
       └─────────────┘             └──────┬──────┘
                                          │
                            ┌─────────────┼─────────────┐
                            │             │             │
                            ▼             ▼             ▼
                     PostgreSQL        Redis       Object Storage
                     Neon / Managed    Managed      R2 / S3
```

---

# 51. Environments

The project should support:

```text
Development
Staging
Production
```

## Development

Local machine.

## Staging

Used for testing deployment and integrations.

## Production

Real user data.

Production data must never be used casually during development.

---

# 52. Docker

The backend should be container-ready.

Development may use Docker Compose:

```text
docker-compose

FastAPI
PostgreSQL
Redis
```

Frontend may continue using the existing Vite/TanStack development workflow.

---

# 53. CI/CD

GitHub Actions should eventually handle:

```text
Push
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
Deploy
```

Production deployment should only occur after required checks pass.

---

# 54. Observability

The production system should eventually monitor:

- API latency
- Error rate
- Database performance
- Background job failures
- Import failures
- External provider failures
- Resource utilization

Monitoring should be introduced before the application has significant real-user traffic.

---

# 55. Scalability Strategy

V1 should start simple.

Do NOT begin with microservices.

Recommended architecture:

```text
Modular Monolith
```

One FastAPI application containing clearly separated domains.

Example:

```text
FastAPI
│
├── Auth
├── Users
├── Accounts
├── Transactions
├── Budgets
├── Goals
├── Investments
├── Analytics
├── Reports
├── Notifications
└── News
```

This provides modularity without unnecessary infrastructure complexity.

---

# 56. Future Scaling

If traffic grows significantly:

```text
Current

Single FastAPI Application
        ↓
PostgreSQL
        ↓
Redis
```

Can evolve into:

```text
Load Balancer
      ↓
Multiple FastAPI Instances
      ↓
Shared PostgreSQL
      ↓
Redis
      ↓
Background Workers
```

Specific high-load domains can later be extracted into separate services.

Possible future services:

- Analytics
- News ingestion
- Notifications
- AI
- Investment data

Service extraction should happen only when justified by actual scale or operational requirements.

---

# 57. Why Modular Monolith Instead of Microservices?

MoneyScope V1 does not require microservices.

Microservices would introduce:

- More deployments
- Network communication
- Distributed tracing
- More infrastructure
- More failure modes
- More operational complexity

A modular monolith provides:

- Faster development
- Easier debugging
- Strong domain boundaries
- Simple deployment
- Easier transactions
- Lower cost

Therefore:

> **Start as a modular monolith and extract services only when there is a measurable reason.**

---

# 58. Security Boundary

The system can be viewed as:

```text
                 UNTRUSTED
                    │
                    ▼
              ┌─────────────┐
              │   Browser   │
              └──────┬──────┘
                     │
                   HTTPS
                     │
                     ▼
              ┌─────────────┐
              │   FastAPI   │
              │ Validation  │
              │ Auth        │
              │ Authorization
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │   Service   │
              │   Layer     │
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │ PostgreSQL  │
              └─────────────┘
```

The browser must never be trusted to enforce security rules.

---

# 59. Architectural Principles

MoneyScope follows these principles:

1. Backend is the financial source of truth.
2. Frontend is presentation and interaction.
3. Business logic belongs in services.
4. Database access belongs in repositories.
5. APIs should be versioned.
6. Financial calculations should use Decimal/fixed precision.
7. User ownership must be enforced server-side.
8. Financial mutations must be transactional.
9. Redis is not the source of truth.
10. Background jobs are used for expensive/asynchronous work.
11. External integrations remain behind backend boundaries.
12. Start with a modular monolith.
13. Avoid premature microservices.
14. Keep domains independently testable.
15. Prefer explicit business rules over hidden magic.

---

# 60. Core Data Flow Example

Example: User makes a transaction.

```text
User
 │
 │ Add ₹500 Food Expense
 ▼
Frontend Form
 │
 │ POST /api/v1/transactions
 ▼
FastAPI Router
 │
 │ Validate Request
 ▼
Transaction Service
 │
 ├── Verify Account Ownership
 ├── Verify Category
 ├── Validate Amount
 ├── Determine Transaction Type
 └── Create Transaction
 │
 ▼
Repository
 │
 ▼
PostgreSQL
 │
 ▼
Transaction Created
 │
 ├── Update relevant caches
 ├── Trigger budget evaluation
 └── Trigger notification if required
 │
 ▼
API Response
 │
 ▼
TanStack Query
 │
 ├── Update transaction cache
 ├── Invalidate dashboard
 └── Refresh analytics where required
 │
 ▼
Frontend
```

---

# 61. Core Data Flow — Dashboard

```text
User opens Dashboard
        │
        ▼
TanStack Query
        │
        ▼
GET /api/v1/dashboard/summary
        │
        ▼
Dashboard Service
        │
        ├── Transactions
        ├── Accounts
        ├── Budgets
        ├── Goals
        ├── Investments
        └── Notifications
        │
        ▼
Aggregated Response
        │
        ▼
TanStack Query Cache
        │
        ▼
Dashboard UI
```

The dashboard should not fetch thousands of transactions just to calculate a monthly total in the browser.

---

# 62. Core Data Flow — CSV Import

```text
User
 │
 ▼
CSV Upload
 │
 ▼
FastAPI
 │
 ├── Validate file
 ├── Create import job
 └── Store file
 │
 ▼
Redis Queue
 │
 ▼
Background Worker
 │
 ├── Parse CSV
 ├── Validate rows
 ├── Normalize data
 ├── Detect duplicates
 └── Insert valid transactions
 │
 ▼
PostgreSQL
 │
 ▼
Import Job Status
 │
 ▼
Frontend
```

---

# 63. Core Data Flow — Monthly Report

```text
User
 │
 ▼
Generate Report
 │
 ▼
FastAPI
 │
 ▼
Report Service
 │
 ├── Income
 ├── Expenses
 ├── Savings
 ├── Budget
 ├── Goals
 ├── Investments
 ├── Net Worth
 └── Financial Health
 │
 ▼
Report Generator
 │
 ▼
PDF
 │
 ▼
Object Storage
 │
 ▼
Report Metadata
 │
 ▼
Frontend
```

---

# 64. Architecture Decisions

## Decision 1

Use React/TanStack Start frontend.

**Reason:** Existing Lovable frontend is already built on this architecture.

---

## Decision 2

Use FastAPI backend.

**Reason:** API-first application, Python expertise, strong validation, OpenAPI support, and good async capabilities.

---

## Decision 3

Use PostgreSQL.

**Reason:** Strong relational consistency and excellent support for financial data.

---

## Decision 4

Use SQLAlchemy 2.x.

**Reason:** Explicit ORM behavior, strong typing support, and mature PostgreSQL support.

---

## Decision 5

Use Alembic.

**Reason:** Version-controlled database migrations.

---

## Decision 6

Use Redis.

**Reason:** Caching and background job infrastructure.

---

## Decision 7

Start with a modular monolith.

**Reason:** V1 does not justify microservice complexity.

---

## Decision 8

Use REST APIs.

**Reason:** Simple integration with the existing frontend and easy OpenAPI documentation.

---

## Decision 9

Backend owns financial calculations.

**Reason:** Prevent inconsistent financial logic between frontend clients.

---

## Decision 10

Support manual + CSV transaction ingestion first.

**Reason:** Solves the immediate multi-UPI problem without requiring complex financial integrations.

---

# 65. Architecture Evolution

### V1

```text
PWA
 ↓
FastAPI
 ↓
PostgreSQL
 ↓
Redis
```

### V1.5

```text
PWA
 ↓
FastAPI
 ↓
PostgreSQL
 ↓
Redis
 ↓
Background Workers
 ↓
External Integrations
```

### Future

```text
                    API Gateway
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   Core Finance      Analytics          AI
     Service          Service          Service
        │                │                │
        └────────────┬───┴────────────────┘
                     ▼
                PostgreSQL
                     │
                   Redis
```

Service extraction should only happen when required.

---

# 66. Architecture Boundaries

The following boundaries must remain clear:

```text
Frontend
≠
Backend

API Layer
≠
Business Logic

Business Logic
≠
Database Access

PostgreSQL
≠
Cache

Core Finance
≠
External Providers
```

Clear boundaries make the system easier to test, maintain, and scale.

---

# 67. Final Architecture Statement

MoneyScope V1 will use a **modular monolith architecture** with:

```text
React + TanStack Start
        ↓
TanStack Query
        ↓
REST API
        ↓
FastAPI
        ↓
Domain Services
        ↓
Repositories
        ↓
PostgreSQL
```

with Redis and background workers supporting asynchronous operations and caching.

The architecture is intentionally simple enough for a small development team while providing clear domain boundaries for future growth.

The system should optimize for:

> **Correctness first → Security second → Maintainability third → Performance fourth → Scale when needed.**

MoneyScope should not over-engineer for hypothetical millions of users before achieving a reliable V1.

---

# Document Status

**Status:** Architecture Approved for Database Design

**Next Document:**

`04_Database_Design.md`

The next document will define the actual PostgreSQL schema, entities, relationships, constraints, indexes, financial transaction model, account model, and ER diagram.