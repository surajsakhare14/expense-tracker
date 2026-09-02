import os

os.environ["ENVIRONMENT"] = "testing"

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from alembic import command
from app.core.config import BACKEND_DIR, TEST_DATABASE_NAME, get_settings
from app.core.database import get_db
from app.main import app


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test-only engine after validating its connected database."""
    settings = get_settings()
    engine = create_engine(settings.active_database_url, echo=False)

    with engine.connect() as connection:
        database_name = connection.execute(text("SELECT current_database()")).scalar_one()
    if database_name != TEST_DATABASE_NAME:
        engine.dispose()
        raise RuntimeError("Test database connection did not target the approved test database.")

    alembic_config = Config(str(BACKEND_DIR / "alembic.ini"))
    command.upgrade(alembic_config, "head")

    yield engine
    engine.dispose()


@pytest.fixture
def session(test_db_engine) -> Session:
    """Provide a transaction-bound session that always rolls back test writes."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    TestSessionLocal = sessionmaker(
        bind=connection,
        class_=Session,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    test_session = TestSessionLocal()

    try:
        yield test_session
    finally:
        test_session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(session: Session) -> TestClient:
    """Create test client with database session."""
    def override_get_db():
        yield session
    
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()