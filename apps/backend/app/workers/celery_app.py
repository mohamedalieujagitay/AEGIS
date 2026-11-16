"""Celery application factory for the API (producer) and both worker roles.

Rules (SYSTEM_ARCHITECTURE §2.4 and §6, DECISIONS.md D-055):

- JSON serialization only; pickle can never be accepted.
- No result backend. Assessment results reach the backend through the
  ingestion listener (§6.5), never through Celery.
- Each role has its own exchange and queue namespace (``internal.*``,
  ``assessment.*``) and its own Valkey ACL user, restricted to those keys.
- Remote control, events, mingle and gossip are disabled. They use Valkey
  Pub/Sub and shared keys, which the ACL users are not allowed to touch.
- Task names choose the queue: ``aegis.internal.*`` and ``aegis.assessment.*``.
  A task matching neither cannot be sent, because the default queue does
  not exist and missing queues are never created.

This module must not import database code: the assessment worker imports it
(SYSTEM_ARCHITECTURE §4.5, enforced by import-linter).
"""

from enum import StrEnum
from typing import Any, Final

from celery import Celery
from kombu.entity import Exchange, Queue

from app.broker.config import build_broker_url
from app.core.config import Settings


class WorkerRole(StrEnum):
    """Who is connecting to the broker."""

    API = "api"
    """The backend, which only sends tasks."""

    INTERNAL = "internal"
    """Trusted worker: database access, no outbound internet (D-020)."""

    ASSESSMENT = "assessment"
    """Untrusted worker: outbound access, no database (D-010, D-020)."""


# kombu has no type annotations, hence the narrowly scoped ignores below.
INTERNAL_QUEUE: Final = Queue(  # type: ignore[no-untyped-call]
    "internal.default",
    Exchange("internal", type="direct"),  # type: ignore[no-untyped-call]
    routing_key="internal.default",
)
ASSESSMENT_QUEUE: Final = Queue(  # type: ignore[no-untyped-call]
    "assessment.default",
    Exchange("assessment", type="direct"),  # type: ignore[no-untyped-call]
    routing_key="assessment.default",
)

UNROUTED_QUEUE: Final = "aegis.unrouted"
"""Default queue of the API. It is never declared, so unrouted tasks fail."""

TASK_ROUTES: Final[dict[str, dict[str, str]]] = {
    "aegis.internal.*": {"queue": INTERNAL_QUEUE.name},
    "aegis.assessment.*": {"queue": ASSESSMENT_QUEUE.name},
}

_ROLE_QUEUES: Final[dict[WorkerRole, tuple[Queue, ...]]] = {
    WorkerRole.API: (INTERNAL_QUEUE, ASSESSMENT_QUEUE),
    WorkerRole.INTERNAL: (INTERNAL_QUEUE,),
    WorkerRole.ASSESSMENT: (ASSESSMENT_QUEUE,),
}


def _transport_options(role: WorkerRole, settings: Settings) -> dict[str, Any]:
    options: dict[str, Any] = {
        "socket_connect_timeout": settings.valkey_connect_timeout,
        "socket_timeout": settings.valkey_socket_timeout,
        "health_check_interval": 25,
    }
    if role is not WorkerRole.API:
        # Messages being processed are tracked under the role's own keys, so
        # the roles never share a key (verified against the ACLs, D-055).
        options |= {
            "unacked_key": f"{role}.unacked",
            "unacked_index_key": f"{role}.unacked_index",
            "unacked_mutex_key": f"{role}.unacked_mutex",
        }
    return options


def create_celery_app(role: WorkerRole, settings: Settings) -> Celery:
    """Create the Celery application for ``role``. No connection is opened."""
    queues = _ROLE_QUEUES[role]
    app = Celery(f"aegis-{role}", broker=build_broker_url(settings), set_as_current=False)
    app.conf.update(
        # Serialization: JSON only.
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        result_accept_content=["json"],
        # No result backend.
        result_backend=None,
        task_ignore_result=True,
        task_store_errors_even_if_ignored=False,
        # Queues and routing.
        task_queues=queues,
        task_routes=TASK_ROUTES,
        task_default_queue=queues[0].name if role is not WorkerRole.API else UNROUTED_QUEUE,
        task_create_missing_queues=False,
        # No Pub/Sub or shared keys (the ACL users cannot use them).
        worker_enable_remote_control=False,
        worker_send_task_events=False,
        task_send_sent_event=False,
        # Execution limits (SYSTEM_ARCHITECTURE §6.6).
        task_soft_time_limit=settings.worker_task_soft_time_limit,
        task_time_limit=settings.worker_task_time_limit,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=100,
        worker_cancel_long_running_tasks_on_connection_loss=True,
        # Connections: wait for Valkey at startup and reconnect after outages.
        broker_connection_retry_on_startup=True,
        broker_connection_max_retries=None,
        broker_connection_timeout=settings.valkey_connect_timeout,
        broker_transport_options=_transport_options(role, settings),
        # AEGIS configures logging itself (app.core.logging).
        worker_hijack_root_logger=False,
        enable_utc=True,
        timezone="UTC",
    )
    return app
