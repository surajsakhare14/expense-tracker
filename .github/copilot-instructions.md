# MoneyScope — GitHub Copilot Project Instructions

## 1. Project Identity

MoneyScope is a personal finance management application focused on an Indian/UPI-centric experience.

The product includes:

- Dashboard
- Transactions
- Analytics
- Budgets
- Savings goals
- Investments
- Finance news
- User settings and preferences

This is a production-oriented application, not a demo-only CRUD project.

The authoritative project documentation is under `docs/`.

Before making architectural or cross-cutting changes, read the relevant documents in `docs/`.

---

## 2. Repository Structure

```text
MoneyScope/
├── frontend/       # React + TanStack Start frontend
├── backend/        # FastAPI backend
├── docs/           # Authoritative product and technical documentation
└── .github/
    └── copilot-instructions.md
```

The frontend and backend are separate applications.

Do not assume they share the same runtime, framework, or deployment model.

---

## 3. Authoritative Documentation

Treat these documents as the primary source of truth:

```text
docs/
├── 00_Project_Context.md
├── 01_Product_Vision.md
├── 02_Feature_Freeze_V1.md
├── 03_System_Architecture.md
├── 04_Database_Design.md
├── 05_API_Contracts.md
├── 06_Backend_Architecture.md
└── 07_Development_Roadmap.md
```

When implementing a feature:

1. Read the relevant documentation first.
2. Inspect the existing code.
3. Identify the smallest correct implementation.
4. Do not invent conflicting architecture.
5. If the documentation and existing code conflict, stop and explain the conflict before making a broad architectural change.

Do not silently change product scope.

---

## 4. Frontend Stack

The frontend currently uses:

- React 19
- TypeScript
- TanStack Start
- TanStack Router
- TanStack React Query
- Vite
- Tailwind CSS v4
- Recharts
- Radix UI / shadcn-style components
- React Hook Form
- Zod
- Lucide icons

The frontend originated from Lovable and is feature-frozen for V1.

Current major routes include:

```text
/
/transactions
/analytics
/goals
/investments
/news
/settings
```

The current frontend contains mock finance data and will progressively be connected to the FastAPI backend.

### Frontend rules

- Do not redesign the UI unless explicitly requested.
- Do not change the visual language unnecessarily.
- Preserve the existing route structure.
- Do not replace the frontend framework.
- Do not introduce a second state-management architecture without a documented reason.
- Prefer the existing TanStack Query setup for server state.
- Preserve responsive desktop/mobile behavior.
- Do not modify generated TanStack files manually unless absolutely necessary.

Backend integration should change data sources and behavior without unnecessarily changing the existing UI.

---

## 5. Backend Stack

The backend is a separate FastAPI application under:

```text
backend/
```

Current backend foundation:

- Python 3.11+
- FastAPI
- Uvicorn
- SQLAlchemy 2.x
- PostgreSQL
- psycopg 3
- Alembic
- Pydantic v2
- pydantic-settings
- Pytest
- Ruff

The backend architecture is a modular monolith.

### Backend rules

- Do not introduce microservices unless explicitly requested.
- Keep domain modules separated by responsibility.
- Keep HTTP/API concerns separate from database and business logic.
- Prefer dependency injection through FastAPI dependencies.
- Keep configuration and secrets in environment variables.
- Do not hard-code credentials or API keys.
- Use type hints throughout backend code.
- Prefer small, testable functions over large route handlers.

---

## 6. Database Rules

PostgreSQL is the primary database.

SQLAlchemy 2.x is the ORM.

Alembic is the migration system.

There must be exactly one authoritative SQLAlchemy declarative `Base` and metadata source.

### Schema-change workflow

For every database schema change:

1. Modify the SQLAlchemy model.
2. Generate an Alembic migration.
3. Review the generated migration manually.
4. Confirm the migration does not contain unintended changes.
5. Run the migration against the development PostgreSQL database.
6. Run relevant tests.
7. Commit the model and migration together.

Never manually create application tables in PostgreSQL as a replacement for Alembic.

Never silently modify an already-applied migration.

If a migration is required, explicitly tell the developer that a new file under:

```text
backend/alembic/versions/
```

will be created.

---

## 7. Environment and Secrets

Use environment configuration through `pydantic-settings`.

Typical local configuration belongs in:

```text
backend/.env
```

The repository-safe template belongs in:

```text
backend/.env.example
```

Never commit:

- passwords
- API keys
- JWT secrets
- provider credentials
- database credentials
- private tokens

`.env.example` must contain placeholders only.

Local development databases may use different credentials on different laptops. That is expected.

Database credentials are environment-specific; database schema and migrations are repository-controlled.

---

## 8. Authentication

Authentication is part of the planned backend architecture.

When authentication is implemented:

- Use the documented authentication design.
- Scope user-owned data to the authenticated user.
- Never trust a client-supplied `user_id` for ownership.
- Validate ownership on every resource mutation.
- Keep password hashing and token handling server-side.
- Never log passwords, tokens, or sensitive authentication data.

Do not add authentication dependencies before the roadmap phase that requires them unless explicitly requested.

---

## 9. API Design

Follow `docs/05_API_Contracts.md` as the API contract source of truth.

General principles:

- Use versioned APIs.
- Keep resource naming consistent.
- Prefer RESTful resource endpoints for CRUD.
- Use dedicated summary/aggregation endpoints where the UI requires computed financial data.
- Return predictable response shapes.
- Validate request data with Pydantic.
- Use appropriate HTTP status codes.
- Do not expose database models directly when a dedicated response schema is appropriate.
- Do not leak internal implementation details through API responses.

For errors, preserve the project's standardized error envelope.

Validation errors should be machine-readable enough for the frontend to display useful messages.

---

## 10. Money and Financial Data

Money calculations require particular care.

- Do not use floating-point arithmetic for persisted monetary values or financial calculations where exactness matters.
- Prefer PostgreSQL `NUMERIC` / SQLAlchemy `Numeric` for monetary amounts.
- Use explicit currency handling.
- Do not silently mix currencies.
- Define rounding behavior explicitly.
- Avoid duplicating financial calculations across frontend and backend.
- The backend should be the source of truth for financial calculations and aggregates.

The frontend may format amounts for display, but authoritative financial calculations belong to the backend.

---

## 11. Transactions

Transactions are a core domain and source of truth for many analytics features.

When implementing transactions:

- Preserve user ownership.
- Validate amount, direction, date, category, and source/provider fields.
- Support pagination for transaction lists.
- Avoid loading an entire user's transaction history unnecessarily.
- Use database indexes for frequently filtered fields.
- Handle duplicate imports safely.
- Treat CSV imports as a controlled workflow rather than blindly inserting every row.

Any transaction mutation must be tested.

---

## 12. Goals, Budgets, Investments, and Analytics

These domains depend on consistent financial data.

### Goals

Goals should have clear ownership, target amounts, saved amounts, deadlines, status, and contribution history where applicable.

### Budgets

Budget calculations must define:

- Budget period
- Total budget
- Category budgets where supported
- Actual spending
- Remaining amount
- Utilization percentage
- Over-budget behavior

### Investments

Investment valuation must clearly distinguish:

- Invested amount
- Current value
- Profit/loss
- Return percentage
- Asset type

Do not invent external market-data integrations without explicit approval.

### Analytics

Analytics should use backend aggregation rather than downloading large raw datasets to the frontend.

---

## 13. API Versioning

The backend uses a versioned API structure.

Keep versioned routes under:

```text
backend/app/api/v1/
```

Do not place domain endpoints randomly throughout the project.

When adding a domain:

```text
app/
├── api/
│   └── v1/
├── core/
├── models/
└── ...
```

Follow the documented backend architecture for schemas, services, repositories, and domain modules as those phases are introduced.

---

## 14. Testing

Testing is required for meaningful backend changes.

At minimum, add or update tests for:

- API behavior
- validation
- authentication/authorization
- database behavior
- important business rules
- financial calculations
- migration-related behavior where appropriate

Run:

```bash
pytest
```

Run Ruff:

```bash
ruff check .
```

For API changes, also verify the generated OpenAPI schema when appropriate.

Do not mark work complete when tests are failing unless the failure is explicitly documented and accepted.

---

## 15. Alembic Migration Safety

Before creating a migration:

```bash
alembic revision --autogenerate -m "description"
```

Then inspect the generated file.

Never blindly trust autogenerate.

Check for:

- unintended table changes
- unintended column changes
- missing indexes
- missing foreign keys
- incorrect nullability
- incorrect numeric types
- destructive operations

Then apply:

```bash
alembic upgrade head
```

Check:

```bash
alembic current
```

When appropriate, inspect the actual PostgreSQL schema after migration.

---

## 16. Code Quality

Use the existing project conventions.

Prefer:

- clear names
- explicit types
- small functions
- dependency injection
- reusable domain logic
- consistent error handling
- explicit validation
- readable SQLAlchemy queries

Avoid:

- unnecessary abstractions
- premature optimization
- duplicated business logic
- global mutable state
- hard-coded environment-specific values
- giant route handlers
- unnecessary dependencies

Do not introduce a library simply because it is popular. Explain why it is needed.

---

## 17. Scope Control

MoneyScope follows a phased development roadmap.

When working on a specific phase:

- Implement only the requested phase unless explicitly told otherwise.
- Do not jump ahead and implement later features.
- Do not add Redis, workers, external providers, authentication, or financial domains early just because they may eventually be useful.
- Keep commits logically grouped by milestone.

If you notice a future requirement while implementing the current phase, mention it rather than silently implementing it.

---

## 18. Git and Collaboration

The project may be developed from multiple laptops.

Git is the source of truth for code, migrations, and documentation.

Before starting work on another machine:

```bash
git pull
```

After completing a logical milestone:

```bash
git status
git diff
git add .
git commit -m "..."
git push
```

Do not commit local `.env` files.

Do not commit virtual environments:

```text
venv/
.venv/
```

Do not commit Python cache/build artifacts.

Do not assume Copilot chat/session history is synchronized between laptops. The repository documentation and this file must contain the durable project context.

---

## 19. Copilot Working Modes

Use the following workflow:

### Ask mode

Use for:

- Understanding existing code
- Explaining errors
- Reviewing a function
- Asking architectural questions
- Inspecting behavior without changing files

### Plan mode

Use for:

- New phases
- Database design changes
- Cross-module changes
- Authentication architecture
- API architecture
- Large refactors

Plan mode should inspect the repository and relevant `docs/` files before proposing implementation.

### Agent mode

Use for:

- Implementing an approved plan
- Creating/modifying files
- Creating migrations
- Running tests
- Fixing implementation issues
- Completing a defined milestone

Agent mode must stay within the approved scope.

---

## 20. Required Behavior Before Coding

For any significant feature, Copilot should:

1. Read the relevant documentation.
2. Inspect the existing implementation.
3. Identify affected files.
4. Explain the intended changes or create a plan when appropriate.
5. Check for existing patterns before introducing new ones.
6. Implement the smallest coherent change.
7. Run relevant tests and quality checks.
8. Report:
   - files created
   - files modified
   - migrations created
   - tests run
   - test results
   - remaining issues

Do not claim verification if commands were not actually executed.

---

## 21. Phase 1 Baseline

Phase 1 backend foundation has already been implemented and committed.

It includes:

- FastAPI application
- Configuration
- PostgreSQL/SQLAlchemy foundation
- Alembic
- Health endpoint
- API versioning foundation
- Error handling
- Logging
- Tests
- Ruff configuration

The Phase 1 baseline migration intentionally contains no domain tables.

Do not recreate or replace the Phase 1 baseline migration.

The next planned work is Phase 2 according to:

```text
docs/07_Development_Roadmap.md
```

---

## 22. Important Rule

When unsure, do not guess.

First inspect:

```text
docs/
backend/
frontend/
```

Then explain the ambiguity and ask for approval if the decision would affect architecture, database schema, API contracts, security, or product scope.
