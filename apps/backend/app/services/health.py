"""Readiness checks for the API's dependencies.

Each check runs a blocking probe (``Database.ping()``, ``Broker.ping()``) in
a worker thread with a time limit. A probe that does not finish in time is
abandoned and the dependency is reported unavailable, so a readiness request
never takes much longer than the configured timeout.

Concurrent requests share one evaluation, and its result is reused for a
short time. Frequent probes therefore cannot open many connections or tie up
many threads while a dependency is down.

Failures are logged with the exception type only: driver messages can contain
host names and other connection details. Changes of the overall state are
logged once: WARNING when the service stops being ready (with the
unavailable dependencies), INFO when it becomes ready.
"""

import logging
import time
from collections.abc import Callable, Mapping

import anyio
import anyio.to_thread

from app.schemas.health import CheckStatus

logger = logging.getLogger("app.health")

Probe = Callable[[], None]
"""A blocking check that returns normally when the dependency is available."""

DEFAULT_CACHE_SECONDS = 1.0


class ReadinessChecker:
    def __init__(
        self,
        probes: Mapping[str, Probe],
        timeout: float,
        cache_seconds: float = DEFAULT_CACHE_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._probes = dict(probes)
        self._timeout = timeout
        self._cache_seconds = cache_seconds
        self._clock = clock
        self._lock = anyio.Lock()
        self._cached: dict[str, CheckStatus] | None = None
        self._cached_at = 0.0
        self._last_ready: bool | None = None

    async def check(self) -> dict[str, CheckStatus]:
        """Return the status of every dependency, evaluating them at most once per cache period."""
        async with self._lock:
            now = self._clock()
            if self._cached is not None and now - self._cached_at < self._cache_seconds:
                return dict(self._cached)
            results: dict[str, CheckStatus] = {}
            async with anyio.create_task_group() as group:
                for name, probe in self._probes.items():
                    group.start_soon(self._run, name, probe, results)
            self._cached = results
            self._cached_at = self._clock()
            self._log_transition(results)
            return dict(results)

    def _log_transition(self, results: dict[str, CheckStatus]) -> None:
        failed = sorted(name for name, status in results.items() if status != "ok")
        ready = not failed
        if ready == self._last_ready:
            return
        self._last_ready = ready
        if ready:
            logger.info("Service is ready", extra={"event": "health.ready"})
        else:
            logger.warning(
                "Service is not ready",
                extra={"event": "health.not_ready", "unavailable": failed},
            )

    async def _run(self, name: str, probe: Probe, results: dict[str, CheckStatus]) -> None:
        status: CheckStatus = "unavailable"
        with anyio.move_on_after(self._timeout) as scope:
            try:
                await anyio.to_thread.run_sync(probe, abandon_on_cancel=True)
                status = "ok"
            except Exception as exc:
                logger.warning(
                    "Readiness check failed",
                    extra={
                        "event": "health.check_failed",
                        "dependency": name,
                        "error_type": type(exc).__name__,
                    },
                )
        if scope.cancelled_caught:
            logger.warning(
                "Readiness check timed out",
                extra={"event": "health.check_timeout", "dependency": name},
            )
        results[name] = status
