import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.database import get_db
from app.main import app
from app.models.base import Base


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine."""
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)

    # Create all tables needed by tests.
    Base.metadata.create_all(bind=engine)
    yield engine

@pytest.fixture(autouse=True)
def cleanup_db(test_db_engine):
    """Clean up database tables before each test."""
    # Delete all data from tables (in reverse order of dependencies)
    with test_db_engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()
    yield


@pytest.fixture
def session(test_db_engine) -> Session:
    """Create a test database session."""
    TestSessionLocal = sessionmaker(bind=test_db_engine, expire_on_commit=False)
    session = TestSessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def client(session: Session) -> TestClient:
    """Create test client with database session."""
    def override_get_db():
        yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()