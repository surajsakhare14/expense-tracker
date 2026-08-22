# MoneyScope Backend

Phase 1 establishes the FastAPI application foundation. Domain models and business modules are intentionally not included yet.

## Requirements

- Python 3.11 or newer
- PostgreSQL 14 or newer for database verification

## Setup

From the `backend/` directory:

```text
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and set `DATABASE_URL` to a development PostgreSQL database. The application does not connect to PostgreSQL merely by being imported; a connection is opened when a session is requested.

## Run

```text
uvicorn app.main:app --reload
```

The development API exposes `GET /health`, `/docs`, `/redoc`, and `/openapi.json` on port 8000.

## Tests and checks

```text
pytest
ruff check .
```

## Alembic

Alembic uses the same `Base.metadata` defined in `app/models/base.py`. Run `alembic upgrade head` against a development database. Phase 1 has no domain models, so a fresh database should remain without application domain tables.

## Scope boundary

This milestone does not include authentication, domain tables, financial modules, Redis, workers, or frontend integration.