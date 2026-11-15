"""Version 1 of the public API, served under ``/api/v1``.

Each feature adds its router module to this package and registers it in
``ROUTERS``. Routes are added by the roadmap tasks that implement them; the
first are the health checks (task 1.5) and authentication (Phase 02).
"""

from fastapi import APIRouter

ROUTERS: list[APIRouter] = []
"""Feature routers included in the version 1 API, in registration order."""
