from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[2]
TEST_DATABASE_NAME = "moneyscope_test"


class Settings(BaseSettings):
    environment: Literal["development", "testing", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    database_url: str | None = None
    test_database_url: str | None = None
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )
    # JWT Configuration
    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = "HS256"
    token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    password_min_length: int = 8
    password_max_length: int = 255

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("environment", "log_level")
    @classmethod
    def normalize_text_settings(cls, value: str) -> str:
        return value.strip()

    @field_validator("database_url", "test_database_url")
    @classmethod
    def normalize_database_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def validate_database_configuration(self) -> "Settings":
        if self.environment == "testing":
            validate_test_database_url(self.test_database_url, self.database_url)
        elif not self.database_url:
            raise ValueError("DATABASE_URL must be configured outside testing.")
        return self

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, value: str, info) -> str:
        value = value.strip()
        if not value or value == "change-me-in-production":
            if info.data.get("environment") == "production":
                raise ValueError("JWT_SECRET_KEY must be set to a secure value in production.")
        return value

    @property
    def active_database_url(self) -> str:
        """Return the only database URL permitted for the active environment."""
        if self.environment == "testing":
            return validate_test_database_url(self.test_database_url, self.database_url)
        if not self.database_url:
            raise ValueError("DATABASE_URL must be configured outside testing.")
        return self.database_url


def validate_test_database_url(test_database_url: str | None, database_url: str | None) -> str:
    """Validate the explicit, allowlisted database URL used by pytest."""
    if not test_database_url:
        raise ValueError("TEST_DATABASE_URL must be configured for testing.")

    try:
        test_url = make_url(test_database_url)
    except Exception as exc:
        raise ValueError("TEST_DATABASE_URL must be a valid PostgreSQL URL.") from exc

    if test_url.get_backend_name() != "postgresql" or test_url.database != TEST_DATABASE_NAME:
        raise ValueError(
            f"TEST_DATABASE_URL must target PostgreSQL database '{TEST_DATABASE_NAME}'."
        )

    if database_url:
        try:
            development_url = make_url(database_url)
        except Exception as exc:
            raise ValueError("DATABASE_URL must be a valid database URL.") from exc
        if _database_target(test_url) == _database_target(development_url):
            raise ValueError("TEST_DATABASE_URL must not target the development database.")

    return test_url.render_as_string(hide_password=False)


def _database_target(url) -> tuple[str, str | None, int | None, str | None]:
    return (url.get_backend_name(), url.host, url.port, url.database)


@lru_cache
def get_settings() -> Settings:
    return Settings()