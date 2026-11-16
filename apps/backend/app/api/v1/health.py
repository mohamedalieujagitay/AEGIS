"""Health check endpoints (SYSTEM_ARCHITECTURE §12.4).

- ``/health/live``: liveness. The process is running and serving HTTP. It
  checks no dependencies, so a database or broker outage never makes an
  orchestrator restart a healthy API process.
- ``/health/ready``: readiness. PostgreSQL and Valkey are reachable, so the
  API can serve requests. 503 otherwise, in the standard error format.

Responses name dependencies only: no hosts, versions or error messages.
Normal results are routine probes and are logged at DEBUG (D-060); readiness
changes and dependency failures are logged by the readiness checker.
"""

from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.errors import error_response
from app.core.request_context import mark_routine_probe
from app.schemas.errors import ErrorDetail, ErrorResponse
from app.schemas.health import LivenessResponse, ReadinessChecks, ReadinessResponse
from app.services.health import ReadinessChecker

router = APIRouter(prefix="/health", tags=["health"])

NO_STORE = {"Cache-Control": "no-store"}
NOT_READY_RESPONSES: dict[int | str, dict[str, Any]] = {
    503: {"model": ErrorResponse, "description": "A dependency is unavailable."},
}


@router.get("/live", response_model=LivenessResponse, summary="Liveness check")
def live(request: Request) -> JSONResponse:
    mark_routine_probe(request.state)
    return JSONResponse(LivenessResponse(status="ok").model_dump(), headers=NO_STORE)


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses=NOT_READY_RESPONSES,
    summary="Readiness check",
)
async def ready(request: Request) -> JSONResponse:
    checker: ReadinessChecker = request.app.state.readiness
    results = await checker.check()
    failed = sorted(name for name, status in results.items() if status != "ok")
    mark_routine_probe(request.state)
    if failed:
        return error_response(
            request,
            HTTPStatus.SERVICE_UNAVAILABLE,
            "service_not_ready",
            "The service is not ready.",
            details=[
                ErrorDetail(location=[name], message="unavailable", type="dependency_unavailable")
                for name in failed
            ],
            headers=NO_STORE,
        )
    body = ReadinessResponse(status="ready", checks=ReadinessChecks.model_validate(results))
    return JSONResponse(body.model_dump(), headers=NO_STORE)
