"""Celery application skeleton, worker entry points and health checks.

No broker is needed: these tests check configuration only. Message flow
through Valkey with the real ACL users is tested by the container smoke test
(infrastructure/scripts/smoke_test.py).
"""

import importlib
import json
import logging
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from celery.exceptions import QueueNotFound
from pydantic import SecretStr

from app import healthcheck as api_healthcheck
from app.core.config import Environment, Settings
from app.core.logging import HANDLER_NAME
from app.workers import healthcheck as worker_healthcheck
from app.workers.celery_app import (
    ASSESSMENT_QUEUE,
    INTERNAL_QUEUE,
    UNROUTED_QUEUE,
    WorkerRole,
    create_celery_app,
)
from app.workers.heartbeat import (
    FUTURE_TOLERANCE_SECONDS,
    HEARTBEAT_INTERVAL_SECONDS,
    HEARTBEAT_MAX_AGE_SECONDS,
    install_heartbeat,
    is_fresh,
    touch,
)


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "environment": Environment.TEST,
        "valkey_host": "valkey",
        "valkey_username": "worker",
        "valkey_password": SecretStr("worker-secret"),
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


# --- Celery configuration ---------------------------------------------------


@pytest.mark.parametrize("role", list(WorkerRole))
def test_every_role_uses_json_only_and_no_result_backend(role: WorkerRole) -> None:
    conf = create_celery_app(role, _settings()).conf
    assert conf.task_serializer == "json"
    assert conf.result_serializer == "json"
    assert list(conf.accept_content) == ["json"]
    assert list(conf.result_accept_content) == ["json"]
    assert conf.result_backend is None
    assert conf.task_ignore_result is True


@pytest.mark.parametrize("role", list(WorkerRole))
def test_every_role_avoids_pubsub_and_shared_keys(role: WorkerRole) -> None:
    conf = create_celery_app(role, _settings()).conf
    assert conf.worker_enable_remote_control is False
    assert conf.worker_send_task_events is False
    assert conf.task_send_sent_event is False
    assert conf.task_create_missing_queues is False
    assert conf.broker_connection_retry_on_startup is True


@pytest.mark.parametrize(
    ("role", "queues", "unacked_prefix"),
    [
        (WorkerRole.INTERNAL, ["internal.default"], "internal."),
        (WorkerRole.ASSESSMENT, ["assessment.default"], "assessment."),
    ],
)
def test_workers_consume_only_their_own_namespace(
    role: WorkerRole, queues: list[str], unacked_prefix: str
) -> None:
    conf = create_celery_app(role, _settings()).conf
    assert [queue.name for queue in conf.task_queues] == queues
    assert conf.task_default_queue == queues[0]
    options = conf.broker_transport_options
    for key in ("unacked_key", "unacked_index_key", "unacked_mutex_key"):
        assert options[key].startswith(unacked_prefix)


def test_api_can_send_to_both_namespaces_but_has_no_default_queue() -> None:
    app = create_celery_app(WorkerRole.API, _settings())
    assert {queue.name for queue in app.conf.task_queues} == {
        INTERNAL_QUEUE.name,
        ASSESSMENT_QUEUE.name,
    }
    assert app.conf.task_default_queue == UNROUTED_QUEUE
    assert UNROUTED_QUEUE not in app.amqp.queues
    assert "unacked_key" not in app.conf.broker_transport_options


@pytest.mark.parametrize(
    ("task_name", "queue"),
    [
        ("aegis.internal.generate_report", "internal.default"),
        ("aegis.assessment.dns_inspection", "assessment.default"),
    ],
)
def test_task_names_choose_the_queue(task_name: str, queue: str) -> None:
    app = create_celery_app(WorkerRole.API, _settings())
    route = app.amqp.router.route({}, task_name)
    assert route["queue"].name == queue


def test_unrouted_tasks_cannot_be_sent() -> None:
    app = create_celery_app(WorkerRole.API, _settings())
    with pytest.raises(QueueNotFound):
        app.amqp.router.route({}, "something.else")


def test_time_limits_come_from_settings() -> None:
    conf = create_celery_app(
        WorkerRole.ASSESSMENT,
        _settings(worker_task_soft_time_limit=30, worker_task_time_limit=45),
    ).conf
    assert (conf.task_soft_time_limit, conf.task_time_limit) == (30, 45)
    assert conf.worker_prefetch_multiplier == 1


def test_broker_password_is_masked_in_celery_output() -> None:
    app = create_celery_app(WorkerRole.INTERNAL, _settings())
    uri = app.connection_for_write().as_uri()
    assert "worker-secret" not in uri
    assert uri == "redis://worker:**@valkey:6379/0"


# --- Heartbeat --------------------------------------------------------------


def _heartbeat_at(path: Path, modified: float) -> None:
    """Write a heartbeat file whose modification time is exactly ``modified``."""
    touch(path)
    os.utime(path, (modified, modified))


def test_missing_heartbeat_is_not_fresh(tmp_path: Path) -> None:
    assert is_fresh(tmp_path / "heartbeat") is False


@pytest.mark.parametrize(
    ("age", "fresh"),
    [
        (0.0, True),  # written this instant
        (HEARTBEAT_INTERVAL_SECONDS, True),  # one interval old
        (HEARTBEAT_MAX_AGE_SECONDS, True),  # exactly at the limit
        (HEARTBEAT_MAX_AGE_SECONDS + 0.5, False),  # stale
        (HEARTBEAT_MAX_AGE_SECONDS + 3600, False),  # long dead
        (-0.000001, True),  # file time a fraction later than the clock (Windows)
        (-1.0, True),  # small clock step backwards
        (-FUTURE_TOLERANCE_SECONDS, True),  # exactly at the future tolerance
        (-(FUTURE_TOLERANCE_SECONDS + 0.5), False),  # too far in the future
        (-3600.0, False),  # clock far in the past: not trusted
    ],
)
def test_heartbeat_freshness_by_age(tmp_path: Path, age: float, fresh: bool) -> None:
    """``age`` is how long before ``now`` the heartbeat was written (negative: after)."""
    beat = tmp_path / "heartbeat"
    now = 1_700_000_000.0
    _heartbeat_at(beat, now - age)
    assert is_fresh(beat, now=now) is fresh


def test_heartbeat_written_now_is_fresh_regardless_of_clock_rounding(tmp_path: Path) -> None:
    """The real clocks: a file written just now must never be considered stale.

    On Windows the file time can be a fraction of a microsecond later than
    ``time.time()``; repeated writes make that case occur deterministically
    often enough to catch a regression without any sleep.
    """
    beat = tmp_path / "heartbeat"
    for _ in range(500):
        touch(beat)
        assert is_fresh(beat) is True


class _FakeTimer:
    def __init__(self) -> None:
        self.calls: list[tuple[float, Any]] = []
        self.cancelled = False

    def call_repeatedly(self, interval: float, fun: Any, args: Any, priority: int) -> "_FakeTimer":
        self.calls.append((interval, fun))
        return self

    def cancel(self) -> None:
        self.cancelled = True


def test_heartbeat_step_touches_the_file_while_consuming(tmp_path: Path) -> None:
    beat = tmp_path / "heartbeat"
    app = create_celery_app(WorkerRole.INTERNAL, _settings())
    install_heartbeat(app, beat)
    [step_class] = list(app.steps["consumer"])

    class Consumer:
        timer = _FakeTimer()

    consumer = Consumer()
    step = step_class(consumer)
    step.start(consumer)
    assert is_fresh(beat)
    assert len(consumer.timer.calls) == 1
    assert consumer.timer.calls[0][0] == 10.0

    step.stop(consumer)
    assert consumer.timer.cancelled
    assert not beat.exists()


def test_worker_healthcheck_command(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    beat = tmp_path / "heartbeat"
    monkeypatch.setenv("AEGIS_WORKER_HEARTBEAT_FILE", str(beat))
    assert worker_healthcheck.main() == 1
    touch(beat)
    assert worker_healthcheck.main() == 0


# --- Worker entry points ----------------------------------------------------


def _import_worker(monkeypatch: pytest.MonkeyPatch, role: str) -> ModuleType:
    for name, value in {
        "AEGIS_ENVIRONMENT": "test",
        "AEGIS_LOG_FORMAT": "json",
        "AEGIS_VALKEY_HOST": "valkey",
        "AEGIS_VALKEY_USERNAME": f"worker-{role}",
        "AEGIS_VALKEY_PASSWORD": "secret",
    }.items():
        monkeypatch.setenv(name, value)
    module_name = f"app.workers.{role}.worker"
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


@pytest.mark.parametrize("role", ["internal", "assessment"])
def test_worker_entry_points(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], role: str
) -> None:
    module = _import_worker(monkeypatch, role)
    app = module.app
    assert [queue.name for queue in app.conf.task_queues] == [f"{role}.default"]
    assert [step.__name__ for step in app.steps["consumer"]] == ["HeartbeatStep"]

    # The worker logs as its own service, through the AEGIS handler.
    module._configure_logging()
    logging.getLogger("app.workers").info("probe")
    line = capsys.readouterr().out.strip().splitlines()[-1]
    assert json.loads(line)["service"] == f"aegis-worker-{role}"
    root = logging.getLogger()
    for handler in [h for h in root.handlers if h.get_name() == HANDLER_NAME]:
        root.removeHandler(handler)


# --- API health check command -------------------------------------------------


def test_api_healthcheck_rejects_unknown_checks() -> None:
    assert api_healthcheck.main(["healthcheck", "everything"]) == 2


def test_api_healthcheck_fails_when_the_api_is_not_running(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(api_healthcheck, "API_PORT", 1)
    assert api_healthcheck.main(["healthcheck", "live"]) == 1
