import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.config import Settings
from app.core.database import Base, engine

DEVELOPMENT_DATABASE_URL = "postgresql+psycopg://user:password@localhost:5432/moneyscope"


def test_application_startup(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "MoneyScope API"
    assert "/health" in response.json()["paths"]


def test_documentation_endpoints(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_settings_parse_comma_separated_origins():
    settings = Settings(
        environment="development",
        database_url=DEVELOPMENT_DATABASE_URL,
        cors_origins="http://localhost:5173, https://app.example.com",
    )

    assert settings.cors_origins == ["http://localhost:5173", "https://app.example.com"]


def test_missing_database_url_fails_clearly(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings(environment="development", _env_file=None)


def test_invalid_log_level_fails_clearly():
    with pytest.raises(ValidationError, match="log_level"):
        Settings(
            environment="development", database_url=DEVELOPMENT_DATABASE_URL, log_level="TRACE"
        )


def test_valid_log_level_is_accepted():
    settings = Settings(
        environment="development", database_url=DEVELOPMENT_DATABASE_URL, log_level="WARNING"
    )

    assert settings.log_level == "WARNING"


def test_http_exception_uses_error_envelope(client):
    client.app.add_api_route(
        "/test-http-exception",
        lambda: (_ for _ in ()).throw(HTTPException(status_code=403, detail="Forbidden")),
        methods=["GET"],
    )

    response = client.get("/test-http-exception")

    assert response.status_code == 403
    assert response.json()["error"] == {
        "code": "HTTP_ERROR",
        "message": "Forbidden",
        "details": None,
        "request_id": response.headers["X-Request-ID"],
    }


def test_cors_allows_configured_origin(client):
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "DELETE" in response.headers["access-control-allow-methods"]


def test_cors_rejects_unconfigured_origin(client):
    response = client.options(
        "/health",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers


def test_single_sqlalchemy_metadata_source():
    from app.models.base import Base as ModelBase

    assert Base is ModelBase
    assert engine.url.get_backend_name() == "postgresql"