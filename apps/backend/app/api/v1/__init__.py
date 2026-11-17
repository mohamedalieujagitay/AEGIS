"""Version 1 of the public API, served under ``/api/v1``.

Each feature adds its router module to this package and registers it in
``ROUTERS``. Routes are added by the roadmap tasks that implement them; the
first are the health checks (task 1.5) and authentication (task 2.1).
"""

from fastapi import APIRouter

from app.api.v1 import admin, auth, health

ROUTERS: list[APIRouter] = [health.router, auth.router, admin.router]
"""Feature routers included in the version 1 API, in registration order."""
