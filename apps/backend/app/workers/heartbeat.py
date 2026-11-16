"""Worker heartbeat for container health checks.

Remote control is disabled (D-055), so ``celery inspect ping`` cannot be
used. Instead, the worker's consumer touches a file every few seconds while
it is connected to the broker. The consumer stops when the connection is
lost, so the file goes stale and the health check fails until it reconnects.

The file lives on the container's tmpfs (``/tmp``); the root filesystem is
read-only.
"""

import logging
import time
from pathlib import Path
from typing import Any, Final

from celery import Celery, bootsteps

logger = logging.getLogger("app.workers")

HEARTBEAT_INTERVAL_SECONDS: Final = 10.0
HEARTBEAT_MAX_AGE_SECONDS: Final = 3 * HEARTBEAT_INTERVAL_SECONDS
"""A heartbeat older than this means the worker is not consuming."""


def touch(path: Path) -> None:
    path.write_text(f"{time.time():.0f}\n", encoding="ascii")


FUTURE_TOLERANCE_SECONDS: Final = HEARTBEAT_INTERVAL_SECONDS
"""How far in the future a heartbeat may be dated and still count as fresh.

A file's modification time and ``time.time()`` come from clocks with
different resolutions (on Windows the file time can be a fraction of a
microsecond later than the wall clock), and the wall clock may be stepped
backwards slightly. A heartbeat further in the future than one interval is
not trusted.
"""


def is_fresh(
    path: Path, max_age: float = HEARTBEAT_MAX_AGE_SECONDS, now: float | None = None
) -> bool:
    """Whether the heartbeat file exists and was updated within ``max_age`` seconds."""
    try:
        modified = path.stat().st_mtime
    except OSError:
        return False
    current = time.time() if now is None else now
    return -FUTURE_TOLERANCE_SECONDS <= current - modified <= max_age


def install_heartbeat(app: Celery, path: Path) -> None:
    """Add the heartbeat step to the worker's consumer (started once connected)."""

    class HeartbeatStep(bootsteps.StartStopStep):  # type: ignore[misc]
        requires = ("celery.worker.consumer.connection:Connection",)

        def __init__(self, parent: Any, **kwargs: Any) -> None:
            super().__init__(parent, **kwargs)
            self._timer_ref: Any = None

        def start(self, parent: Any) -> None:
            touch(path)
            self._timer_ref = parent.timer.call_repeatedly(
                HEARTBEAT_INTERVAL_SECONDS, touch, (path,), priority=10
            )
            logger.info("Worker heartbeat started", extra={"event": "worker.heartbeat_started"})

        def stop(self, parent: Any) -> None:
            if self._timer_ref is not None:
                self._timer_ref.cancel()
                self._timer_ref = None
            path.unlink(missing_ok=True)

        shutdown = stop

    app.steps["consumer"].add(HeartbeatStep)
