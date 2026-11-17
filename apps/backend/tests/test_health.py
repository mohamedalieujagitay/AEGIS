"""Liveness and readiness endpoints, and the readiness checker."""

import logging
import threading
import time

import anyio
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from helpers import AegisTestClient

from app.core.config import Environment, Settings
from app.core.request_context import REQUEST_ID_HEADER
from app.main import create_app
from app.services.health import ReadinessChecker

LIVE = "/api/v1/health/live"
READY = "/api/v1/health/ready"
SECRET_DETAIL = "connection to db.internal:5432 as aegis_app failed"


class FakeDependency:
    """Stands in for ``Database`` or ``Broker`` in tests."""

    def __init__(self, error: Exception | None = None, delay: float = 0.0) -> None:
        self.error = error
        self.delay = delay
        self.calls = 0

    def ping(self) -> None:
        self.calls += 1
        if self.delay:
            time.sleep(self.delay)
        if self.error is not None:
            raise self.error

    def dispose(self) -> None:
        """Called on application shutdown, like the real objects."""


def _app(
    database: FakeDependency | None = None,
    broker: FakeDependency | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    app = create_app(settings or Settings(environment=Environment.TEST))
    app.state.database = database or FakeDependency()
    app.state.broker = broker or FakeDependency()
    return app


# --- Liveness ---------------------------------------------------------------


def test_liveness_reports_ok_without_checking_dependencies() -> None:
    database = FakeDependency(RuntimeError("down"))
    broker = FakeDependency(RuntimeError("down"))
    response = TestClient(_app(database, broker)).get(LIVE)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["cache-control"] == "no-store"
    assert database.calls == broker.calls == 0


# --- Readiness --------------------------------------------------------------


def test_readiness_reports_ready_when_all_dependencies_are_available() -> None:
    response = TestClient(_app()).get(READY)

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"database": "ok", "broker": "ok"}}
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    ("database_down", "broker_down", "failed"),
    [
        (True, False, ["database"]),
        (False, True, ["broker"]),
        (True, True, ["broker", "database"]),
    ],
)
def test_readiness_returns_503_in_the_standard_error_format(
    database_down: bool, broker_down: bool, failed: list[str]
) -> None:
    database = FakeDependency(ConnectionError(SECRET_DETAIL) if database_down else None)
    broker = FakeDependency(ConnectionError(SECRET_DETAIL) if broker_down else None)
    response = TestClient(_app(database, broker)).get(READY)

    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"
    error = response.json()["error"]
    assert error["code"] == "service_not_ready"
    assert error["message"] == "The service is not ready."
    assert error["request_id"] == response.headers[REQUEST_ID_HEADER]
    assert error["details"] == [
        {"location": [name], "message": "unavailable", "type": "dependency_unavailable"}
        for name in failed
    ]


def test_readiness_never_exposes_or_logs_error_details(caplog: pytest.LogCaptureFixture) -> None:
    app = _app(FakeDependency(ConnectionError(SECRET_DETAIL)))
    with caplog.at_level(logging.INFO):
        response = TestClient(app).get(READY)

    assert response.status_code == 503
    assert SECRET_DETAIL not in response.text
    assert "db.internal" not in response.text
    logged = " ".join(str(record.__dict__) for record in caplog.records)
    assert SECRET_DETAIL not in logged
    [failure] = [r for r in caplog.records if getattr(r, "event", None) == "health.check_failed"]
    assert failure.__dict__["dependency"] == "database"
    assert failure.__dict__["error_type"] == "ConnectionError"


def test_readiness_is_bounded_by_the_timeout(caplog: pytest.LogCaptureFixture) -> None:
    slow = FakeDependency(delay=3.0)
    app = _app(slow, settings=Settings(environment=Environment.TEST, health_check_timeout=0.2))

    started = time.monotonic()
    with caplog.at_level(logging.WARNING):
        response = TestClient(app).get(READY)
    elapsed = time.monotonic() - started

    assert response.status_code == 503
    assert response.json()["error"]["details"][0]["location"] == ["database"]
    assert elapsed < 1.5
    assert any(getattr(r, "event", None) == "health.check_timeout" for r in caplog.records)


def test_readiness_reflects_recovery_after_the_cache_period() -> None:
    database = FakeDependency(ConnectionError("down"))
    app = _app(database)
    client = TestClient(app)
    assert client.get(READY).status_code == 503

    database.error = None
    app.state.readiness._cached = None  # skip the 1-second cache in this test
    assert client.get(READY).status_code == 200


def test_readiness_is_documented_with_its_503_response() -> None:
    schema = _app().openapi()
    operation = schema["paths"][READY]["get"]
    reference = operation["responses"]["503"]["content"]["application/json"]["schema"]
    assert reference["$ref"] == "#/components/schemas/ErrorResponse"
    assert "/api/v1/health/live" in schema["paths"]


# --- ReadinessChecker -------------------------------------------------------


def test_checker_reuses_results_within_the_cache_period() -> None:
    probe = FakeDependency()
    now = [100.0]
    checker = ReadinessChecker(
        {"database": probe.ping}, timeout=1.0, cache_seconds=1.0, clock=lambda: now[0]
    )

    assert anyio.run(checker.check) == {"database": "ok"}
    assert anyio.run(checker.check) == {"database": "ok"}
    assert probe.calls == 1

    now[0] += 1.5
    anyio.run(checker.check)
    assert probe.calls == 2


def test_concurrent_checks_share_one_evaluation() -> None:
    probe = FakeDependency(delay=0.2)
    checker = ReadinessChecker({"database": probe.ping}, timeout=2.0)
    results: list[dict[str, str]] = []

    async def run_many() -> None:
        async def one() -> None:
            results.append(dict(await checker.check()))

        async with anyio.create_task_group() as group:
            for _ in range(10):
                group.start_soon(one)

    anyio.run(run_many)
    assert probe.calls == 1
    assert results == [{"database": "ok"}] * 10


def test_checker_runs_probes_concurrently() -> None:
    started: list[float] = []
    lock = threading.Lock()

    def slow_probe() -> None:
        with lock:
            started.append(time.monotonic())
        time.sleep(0.3)

    checker = ReadinessChecker({"a": slow_probe, "b": slow_probe}, timeout=2.0)
    begin = time.monotonic()
    assert anyio.run(checker.check) == {"a": "ok", "b": "ok"}
    assert time.monotonic() - begin < 0.55


# --- Integration --------------------------------------------------------------


def test_readiness_uses_the_real_database(database_settings: Settings) -> None:
    app = create_app(database_settings)
    app.state.broker = FakeDependency()
    with TestClient(app) as client:
        response = client.get(READY)
    assert response.status_code == 200
    assert response.json()["checks"] == {"database": "ok", "broker": "ok"}


def test_readiness_fails_when_nothing_is_configured() -> None:
    response = TestClient(create_app(Settings(environment=Environment.TEST))).get(READY)
    assert response.status_code == 503
    locations = [d["location"] for d in response.json()["error"]["details"]]
    assert locations == [["broker"], ["database"]]


def test_readiness_fails_quickly_when_the_broker_refuses_connections() -> None:
    # Port 1 on the loopback interface refuses connections immediately.
    settings = Settings(environment=Environment.TEST, valkey_host="127.0.0.1", valkey_port=1)
    app = create_app(settings)
    app.state.database = FakeDependency()
    started = time.monotonic()
    response = TestClient(app).get(READY)
    assert response.status_code == 503
    assert response.json()["error"]["details"][0]["location"] == ["broker"]
    assert time.monotonic() - started < settings.health_check_timeout + 1


# --- Logging of health probes (DECISIONS.md D-060) ------------------------------


def _request_records(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if getattr(r, "event", None) == "http.request"]


@pytest.mark.parametrize("path", [LIVE, READY])
def test_routine_probes_are_logged_at_debug_only(
    caplog: pytest.LogCaptureFixture, path: str
) -> None:
    client = TestClient(_app())
    with caplog.at_level(logging.DEBUG, logger="app.request"):
        assert client.get(path).status_code == 200
    [record] = _request_records(caplog)
    assert record.levelno == logging.DEBUG
    assert record.__dict__["path"] == path


def test_not_ready_probe_is_quiet_but_failures_and_transition_are_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = TestClient(_app(FakeDependency(ConnectionError("down"))))
    with caplog.at_level(logging.DEBUG):
        assert client.get(READY).status_code == 503
    [request] = _request_records(caplog)
    assert request.levelno == logging.DEBUG
    events = {getattr(r, "event", None): r for r in caplog.records}
    assert events["health.check_failed"].levelno == logging.WARNING
    assert events["health.not_ready"].levelno == logging.WARNING
    assert events["health.not_ready"].__dict__["unavailable"] == ["database"]


def test_readiness_transitions_are_logged_once_each(caplog: pytest.LogCaptureFixture) -> None:
    database = FakeDependency()
    now = [0.0]
    checker = ReadinessChecker(
        {"database": database.ping}, timeout=1.0, cache_seconds=1.0, clock=lambda: now[0]
    )

    def evaluate() -> None:
        now[0] += 2.0  # past the cache period
        anyio.run(checker.check)

    with caplog.at_level(logging.INFO, logger="app.health"):
        evaluate()  # ready
        evaluate()  # still ready: nothing logged
        database.error = ConnectionError("down")
        evaluate()  # not ready
        evaluate()  # still not ready: only the check failure
        database.error = None
        evaluate()  # ready again

    transitions = [
        (r.__dict__["event"], r.levelno)
        for r in caplog.records
        if r.__dict__.get("event") in ("health.ready", "health.not_ready")
    ]
    assert transitions == [
        ("health.ready", logging.INFO),
        ("health.not_ready", logging.WARNING),
        ("health.ready", logging.INFO),
    ]


def test_unexpected_errors_in_health_endpoints_are_still_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = _app()

    async def broken_check() -> dict[str, str]:
        raise RuntimeError("readiness checker failed")

    app.state.readiness.check = broken_check
    client = TestClient(app, raise_server_exceptions=False)
    with caplog.at_level(logging.INFO):
        response = client.get(READY)

    assert response.status_code == 500
    [request] = _request_records(caplog)
    assert request.levelno == logging.ERROR
    assert any(getattr(r, "event", None) == "error.unhandled" for r in caplog.records)


@pytest.mark.parametrize(
    ("method", "path", "status"),
    [("POST", LIVE, 405), ("GET", "/api/v1/health/unknown", 404)],
)
def test_other_requests_to_health_paths_keep_normal_logging(
    caplog: pytest.LogCaptureFixture, method: str, path: str, status: int
) -> None:
    client = AegisTestClient(_app())
    with caplog.at_level(logging.INFO, logger="app.request"):
        assert client.request(method, path).status_code == status
    [record] = _request_records(caplog)
    assert record.levelno == logging.INFO


def test_marked_probe_with_an_unexpected_status_keeps_its_level() -> None:
    from app.core.request_context import ROUTINE_PROBE_STATE, _log_level

    marked = {"state": {ROUTINE_PROBE_STATE: True}}
    assert _log_level(marked, 200) == logging.DEBUG
    assert _log_level(marked, 503) == logging.DEBUG
    assert _log_level(marked, 500) == logging.ERROR
    assert _log_level(marked, 404) == logging.INFO
    assert _log_level({"state": {}}, 200) == logging.INFO
    assert _log_level({"state": {}}, 503) == logging.ERROR
