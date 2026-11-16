"""Assessment worker (untrusted role) entry point.

    celery --app app.workers.assessment.worker worker
        --without-mingle --without-gossip --without-heartbeat

Consumes only ``assessment.*`` queues as the ``worker-assessment`` Valkey
user. It has no database credentials and is not attached to the ``data``
network (SYSTEM_ARCHITECTURE §6.1). No assessment engines exist yet; they
are added by Phases 03 and 04.
"""

from pathlib import Path
from typing import Any

from celery import signals

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.workers.celery_app import WorkerRole, create_celery_app
from app.workers.heartbeat import install_heartbeat

SERVICE_NAME = "aegis-worker-assessment"

settings = get_settings()
app = create_celery_app(WorkerRole.ASSESSMENT, settings)
install_heartbeat(app, Path(settings.worker_heartbeat_file))


# Celery's signal decorator is untyped; connecting stops Celery configuring logging.
@signals.setup_logging.connect  # type: ignore[untyped-decorator]
def _configure_logging(**_: Any) -> None:
    configure_logging(settings, service=SERVICE_NAME)
