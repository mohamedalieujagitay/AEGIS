"""Internal worker (trusted role) entry point.

    celery --app app.workers.internal.worker worker
        --without-mingle --without-gossip --without-heartbeat

Consumes only ``internal.*`` queues as the ``worker-internal`` Valkey user.
"""

from pathlib import Path
from typing import Any

from celery import signals

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.workers.celery_app import WorkerRole, create_celery_app
from app.workers.heartbeat import install_heartbeat

SERVICE_NAME = "aegis-worker-internal"

settings = get_settings()
app = create_celery_app(WorkerRole.INTERNAL, settings)
install_heartbeat(app, Path(settings.worker_heartbeat_file))


# Celery's signal decorator is untyped; connecting stops Celery configuring logging.
@signals.setup_logging.connect  # type: ignore[untyped-decorator]
def _configure_logging(**_: Any) -> None:
    configure_logging(settings, service=SERVICE_NAME)
