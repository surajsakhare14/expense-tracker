"""Tests for the fail-closed PostgreSQL test database configuration."""

import pytest
from pydantic import ValidationError
from sqlalchemy import text

from app.core.config import TEST_DATABASE_NAME, Settings

DEVELOPMENT_DATABASE_URL = "postgresql+psycopg://user:password@localhost:5432/moneyscope"
TEST_DATABASE_URL = "postgresql+psycopg://user:password@localhost:5432/moneyscope_test"


def test_testing_requires_an_explicit_test_database_url():
    with pytest.raises(ValidationError, match="TEST_DATABASE_URL must be configured"):
        Settings(
            environment="testing", database_url=DEVELOPMENT_DATABASE_URL, test_database_url=None
        )


def test_testing_rejects_development_database_as_test_target():
    with pytest.raises(ValidationError, match="moneyscope_test"):
        Settings(
            environment="testing",
            database_url=DEVELOPMENT_DATABASE_URL,
            test_database_url=DEVELOPMENT_DATABASE_URL,
        )


def test_testing_selects_only_the_explicit_test_database_url():
    settings = Settings(
        environment="testing",
        database_url=DEVELOPMENT_DATABASE_URL,
        test_database_url=TEST_DATABASE_URL,
    )

    assert settings.active_database_url.endswith(f"/{TEST_DATABASE_NAME}")


def test_test_engine_is_connected_only_to_the_approved_database(test_db_engine):
    with test_db_engine.connect() as connection:
        database_name = connection.execute(text("SELECT current_database()")).scalar_one()
    assert database_name == TEST_DATABASE_NAME
