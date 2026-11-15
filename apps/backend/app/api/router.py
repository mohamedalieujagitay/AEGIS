"""Top-level API router.

All public routes are versioned under ``/api/v<n>`` (SYSTEM_ARCHITECTURE.md
§11.1). The internal result-ingestion listener (§6.5) is a separate
application and is never mounted here.
"""

from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter

from app.api import v1
from app.schemas.errors import ErrorResponse

API_V1_PREFIX = "/api/v1"

COMMON_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    422: {"model": ErrorResponse, "description": "The request is invalid."},
    500: {"model": ErrorResponse, "description": "An unexpected error occurred."},
}
"""Documented on every version 1 operation, in the standard error format."""


def build_api_router(v1_routers: Sequence[APIRouter] | None = None) -> APIRouter:
    """Assemble the public API router.

    ``v1_routers`` defaults to the routers registered in ``app.api.v1``. It
    can be overridden to test routing in isolation.
    """
    version_1 = APIRouter(prefix=API_V1_PREFIX, responses=COMMON_ERROR_RESPONSES)
    for router in v1.ROUTERS if v1_routers is None else v1_routers:
        version_1.include_router(router)

    api_router = APIRouter()
    api_router.include_router(version_1)
    return api_router
