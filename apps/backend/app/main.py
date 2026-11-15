"""Application factory.

Run locally from ``apps/backend``::

    uvicorn app.main:create_app --factory --reload

Deployments must add ``--no-server-header`` so the server software is not
disclosed (DECISIONS.md D-042).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.router import build_api_router
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.request_context import RequestContextMiddleware
from app.core.request_limits import RequestBodyLimitMiddleware
from app.database.errors import register_database_exception_handlers
from app.database.session import Database

APP_TITLE = "AEGIS API"
APP_DESCRIPTION = (
    "Self-hosted cybersecurity assessment platform. Every error response uses the "
    "`ErrorResponse` format and includes a request ID, also returned in the "
    "`X-Request-ID` header."
)
API_DOCS_PATH = "/api/docs"
OPENAPI_PATH = "/api/openapi.json"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifecycle.

    No database connection is opened at startup: the engine is created on
    first use. On shutdown, all pooled connections are closed.
    """
    try:
        yield
    finally:
        database: Database = app.state.database
        database.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    ``settings`` defaults to the process-wide settings from the environment.
    Tests pass explicit settings instead.
    """
    resolved = settings if settings is not None else get_settings()
    configure_logging(resolved)

    docs = resolved.docs_enabled
    app = FastAPI(
        title=APP_TITLE,
        description=APP_DESCRIPTION,
        version=__version__,
        debug=resolved.debug,
        lifespan=lifespan,
        license_info={"name": "Apache-2.0", "identifier": "Apache-2.0"},
        # Documentation is disabled in production unless explicitly enabled.
        # ReDoc is not served: Swagger UI covers the same need.
        openapi_url=OPENAPI_PATH if docs else None,
        docs_url=API_DOCS_PATH if docs else None,
        redoc_url=None,
        swagger_ui_parameters={"tryItOutEnabled": False, "persistAuthorization": False},
    )
    app.state.settings = resolved
    app.state.database = Database(resolved)

    register_exception_handlers(app)
    register_database_exception_handlers(app)
    # Middleware added last runs first: the request context wraps everything,
    # so even rejected oversized requests get a request ID and a log entry.
    app.add_middleware(RequestBodyLimitMiddleware, max_body_bytes=resolved.max_request_body_bytes)
    app.add_middleware(RequestContextMiddleware)

    app.include_router(build_api_router())
    return app
