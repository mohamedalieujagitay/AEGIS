"""Application factory.

Run locally from ``apps/backend``::

    uvicorn app.main:create_app --factory --reload

Deployments must add ``--no-server-header`` so the server software is not
disclosed (DECISIONS.md D-042). The container image does (D-051).
"""

import logging
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Final

from fastapi import FastAPI, Response
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.dependencies import AuthContext, InstanceAdmin
from app.api.router import build_api_router
from app.broker.client import Broker
from app.core.config import Environment, Settings, get_settings
from app.core.csrf import CsrfMiddleware
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.request_context import RequestContextMiddleware
from app.core.request_limits import RequestBodyLimitMiddleware
from app.core.security import configure_password_hashing
from app.database.errors import register_database_exception_handlers
from app.database.session import Database
from app.services.health import ReadinessChecker
from app.services.rate_limit import AuthRateLimiter, ValkeyRateLimitStore
from app.services.sessions import SessionPolicy

logger = logging.getLogger("app.main")

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
    """Serve the OpenAPI schema and Swagger UI to instance administrators only.

    The schema maps every endpoint, so it is never public: both routes
    require a signed-in instance administrator (401 or 403 otherwise). The
    vendored Swagger UI assets contain no information about AEGIS.
    """
    app.mount(
        SWAGGER_ASSETS_PATH,
        StaticFiles(directory=SWAGGER_ASSETS_DIR),
        name="swagger-ui-assets",
    )

    @app.get(OPENAPI_PATH, include_in_schema=False)
    def openapi_schema(_: InstanceAdmin, response: Response) -> dict[str, Any]:
        response.headers["Cache-Control"] = "no-store"
        return app.openapi()

    @app.get(API_DOCS_PATH, include_in_schema=False)
    def swagger_ui(_: InstanceAdmin) -> HTMLResponse:
        page = get_swagger_ui_html(
            openapi_url=OPENAPI_PATH,
            title=f"{APP_TITLE} - Swagger UI",
            swagger_js_url=f"{SWAGGER_ASSETS_PATH}/swagger-ui-bundle.js",
            swagger_css_url=f"{SWAGGER_ASSETS_PATH}/swagger-ui.css",
            swagger_favicon_url=f"{SWAGGER_ASSETS_PATH}/favicon-32x32.png",
            swagger_ui_parameters=SWAGGER_UI_PARAMETERS,
        )
        page.headers["Cache-Control"] = "no-store"
        return page


def _secret_key(settings: Settings) -> bytes:
    """The server secret, for CSRF tokens and rate-limit counter names.

    Required in production. Outside production a random key is generated at
    start-up: CSRF tokens then stop working after a restart, and
    rate-limit counters are not shared with other processes that use a different
    key. Sessions and trusted devices are stored in the database and survive a restart.
    """
    if settings.secret_key is not None:
        return settings.secret_key.get_secret_value().encode("utf-8")
    if settings.environment is Environment.PRODUCTION:
        raise RuntimeError(
            "AEGIS_SECRET_KEY is required in production (DECISIONS.md D-065); "
            "provide it as the aegis_secret_key secret file"
        )
    logger.warning(
        "No secret key configured; using a temporary key for this process",
        extra={"event": "auth.ephemeral_secret_key"},
    )
    return secrets.token_bytes(32)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    ``settings`` defaults to the process-wide settings from the environment.
    Tests pass explicit settings instead.
    """
    resolved = settings if settings is not None else get_settings()
    configure_logging(resolved)
    secret = _secret_key(resolved)
    configure_password_hashing(resolved.password_hash_concurrency)

    docs = resolved.docs_enabled
    app = FastAPI(
        title=APP_TITLE,
        description=APP_DESCRIPTION,
        version=__version__,
        debug=resolved.debug,
        lifespan=lifespan,
        license_info={"name": "Apache-2.0", "identifier": "Apache-2.0"},
        # Documentation is disabled in production unless explicitly enabled.
        # When enabled, the schema and Swagger UI are added below, for
        # instance administrators only; ReDoc is not served.
        openapi_url=None,
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
    app.state.auth = AuthContext(
        settings=resolved,
        secret=secret,
        policy=SessionPolicy.from_settings(resolved),
        limiter=AuthRateLimiter(ValkeyRateLimitStore(lambda: app.state.broker), resolved, secret),
    )

    register_exception_handlers(app)
    register_database_exception_handlers(app)
    # Middleware added last runs first: the request context wraps everything,
    # so even rejected oversized requests get a request ID and a log entry.
    # CSRF protection runs innermost, on every state-changing API request.
    app.add_middleware(
        CsrfMiddleware,
        secret=secret,
        session_cookie=resolved.session_cookie_name,
        csrf_cookie=resolved.csrf_cookie_name,
        allowed_origins=resolved.allowed_origin_list,
        max_age=resolved.session_absolute_timeout_hours * 3600,
    )
    app.add_middleware(RequestBodyLimitMiddleware, max_body_bytes=resolved.max_request_body_bytes)
    app.add_middleware(RequestContextMiddleware)

    if docs:
        _add_api_docs(app)
    app.include_router(build_api_router())
    return app
