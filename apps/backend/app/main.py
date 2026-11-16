"""Application factory.

Run locally from ``apps/backend``::

    uvicorn app.main:create_app --factory --reload

Deployments must add ``--no-server-header`` so the server software is not
disclosed (DECISIONS.md D-042). The container image does (D-051).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Final

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.router import build_api_router
from app.broker.client import Broker
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.request_context import RequestContextMiddleware
from app.core.request_limits import RequestBodyLimitMiddleware
from app.database.errors import register_database_exception_handlers
from app.database.session import Database
from app.services.health import ReadinessChecker

APP_TITLE = "AEGIS API"
APP_DESCRIPTION = (
    "Self-hosted cybersecurity assessment platform. Every error response uses the "
    "`ErrorResponse` format and includes a request ID, also returned in the "
    "`X-Request-ID` header."
)
API_DOCS_PATH = "/api/docs"
OPENAPI_PATH = "/api/openapi.json"

# Swagger UI is served from files vendored in the package (DECISIONS.md D-056),
# so opening the documentation never contacts a CDN or other third party.
SWAGGER_ASSETS_DIR: Final = Path(__file__).parent / "static" / "swagger-ui"
SWAGGER_ASSETS_PATH: Final = f"{API_DOCS_PATH}/assets"
SWAGGER_UI_PARAMETERS: Final[dict[str, Any]] = {
    "tryItOutEnabled": False,
    "persistAuthorization": False,
    # Never send the schema URL to the public validator service.
    "validatorUrl": None,
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifecycle.

    No database or broker connection is opened at startup: both are created
    on first use. On shutdown, all pooled connections are closed.
    """
    try:
        yield
    finally:
        database: Database = app.state.database
        database.dispose()
        broker: Broker = app.state.broker
        broker.dispose()


def _add_api_docs(app: FastAPI) -> None:
    """Serve Swagger UI and its assets from this deployment."""
    app.mount(
        SWAGGER_ASSETS_PATH,
        StaticFiles(directory=SWAGGER_ASSETS_DIR),
        name="swagger-ui-assets",
    )

    @app.get(API_DOCS_PATH, include_in_schema=False)
    def swagger_ui() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url=OPENAPI_PATH,
            title=f"{APP_TITLE} - Swagger UI",
            swagger_js_url=f"{SWAGGER_ASSETS_PATH}/swagger-ui-bundle.js",
            swagger_css_url=f"{SWAGGER_ASSETS_PATH}/swagger-ui.css",
            swagger_favicon_url=f"{SWAGGER_ASSETS_PATH}/favicon-32x32.png",
            swagger_ui_parameters=SWAGGER_UI_PARAMETERS,
        )


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
        # Swagger UI is added below with local assets; ReDoc is not served.
        openapi_url=OPENAPI_PATH if docs else None,
        docs_url=None,
        redoc_url=None,
    )
    app.state.settings = resolved
    app.state.database = Database(resolved)
    app.state.broker = Broker(resolved)
    # The probes look up the current objects at call time, so tests can
    # replace app.state.database or app.state.broker.
    app.state.readiness = ReadinessChecker(
        {
            "database": lambda: app.state.database.ping(),
            "broker": lambda: app.state.broker.ping(),
        },
        timeout=resolved.health_check_timeout,
    )

    register_exception_handlers(app)
    register_database_exception_handlers(app)
    # Middleware added last runs first: the request context wraps everything,
    # so even rejected oversized requests get a request ID and a log entry.
    app.add_middleware(RequestBodyLimitMiddleware, max_body_bytes=resolved.max_request_body_bytes)
    app.add_middleware(RequestContextMiddleware)

    if docs:
        _add_api_docs(app)
    app.include_router(build_api_router())
    return app
