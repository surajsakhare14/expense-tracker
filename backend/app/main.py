from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    unexpected_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    application = FastAPI(
        title="MoneyScope API",
        version="0.1.0",
        description="MoneyScope personal finance API.",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    @application.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    application.add_exception_handler(AppException, app_exception_handler)
    application.add_exception_handler(HTTPException, http_exception_handler)
    application.add_exception_handler(Exception, unexpected_exception_handler)
    application.add_exception_handler(422, validation_exception_handler)
    application.include_router(health_router)
    application.include_router(v1_router, prefix="/api/v1")
    logger.info("FastAPI application configured", extra={"environment": settings.environment})
    return application


app = create_app()