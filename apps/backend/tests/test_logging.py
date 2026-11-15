import json
import logging
from collections.abc import Callable
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.logging import (
    HANDLER_NAME,
    HTTP_CLIENT_LOGGERS,
    REDACTED,
    SERVICE_NAME,
    configure_logging,
)
from app.core.request_context import REQUEST_ID_HEADER

MakeApp = Callable[..., FastAPI]


def _json_lines(output: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in output.splitlines() if line.startswith("{")]


def test_records_are_structured_json(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(Settings())
    logging.getLogger("app.test").warning("Something happened", extra={"event": "test.event"})

    [entry] = _json_lines(capsys.readouterr().out)
    assert entry["level"] == "WARNING"
    assert entry["logger"] == "app.test"
    assert entry["service"] == SERVICE_NAME
    assert entry["message"] == "Something happened"
    assert entry["event"] == "test.event"
    assert entry["request_id"] is None
    assert entry["timestamp"].endswith("+00:00")


def test_sensitive_fields_are_redacted(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(Settings())
    logging.getLogger("app.test").info(
        "Login attempt",
        extra={
            "username": "alice",
            "password": "p4ss",
            "api_key": "k-123",
            "session_id": "s-456",
            "authorization": "Bearer t-789",
            "refresh_token": "r-000",
        },
    )

    output = capsys.readouterr().out
    [entry] = _json_lines(output)
    assert entry["username"] == "alice"
    for key in ("password", "api_key", "session_id", "authorization", "refresh_token"):
        assert entry[key] == REDACTED
    for value in ("p4ss", "k-123", "s-456", "t-789", "r-000"):
        assert value not in output


def test_log_level_is_applied(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(Settings(log_level="WARNING"))
    logging.getLogger("app.test").info("hidden")
    logging.getLogger("app.test").warning("shown")
    messages = [e["message"] for e in _json_lines(capsys.readouterr().out)]
    assert messages == ["shown"]


def test_text_format(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(Settings(log_format="text"))
    logging.getLogger("app.test").info("Readable line")
    output = capsys.readouterr().out
    assert "INFO" in output and "app.test" in output and "Readable line" in output
    assert not output.lstrip().startswith("{")


def test_configuring_twice_does_not_duplicate_output(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(Settings())
    configure_logging(Settings())
    assert [h.get_name() for h in logging.getLogger().handlers].count(HANDLER_NAME) == 1
    logging.getLogger("app.test").info("once")
    assert len(_json_lines(capsys.readouterr().out)) == 1


def test_uvicorn_access_log_is_disabled() -> None:
    configure_logging(Settings())
    assert logging.getLogger("uvicorn.access").disabled is True


def test_http_client_url_logging_is_suppressed() -> None:
    configure_logging(Settings())
    for name in HTTP_CLIENT_LOGGERS:
        assert logging.getLogger(name).getEffectiveLevel() == logging.WARNING


def test_each_request_is_logged_once_without_query_string(
    make_app: MakeApp, capsys: pytest.CaptureFixture[str]
) -> None:
    client = TestClient(make_app())
    capsys.readouterr()
    response = client.get("/api/v1/test/items", params={"page": 2, "token": "query-secret"})
    assert response.status_code == 200

    output = capsys.readouterr().out
    assert "query-secret" not in output
    [entry] = [e for e in _json_lines(output) if e.get("event") == "http.request"]
    assert entry["level"] == "INFO"
    assert entry["method"] == "GET"
    assert entry["path"] == "/api/v1/test/items"
    assert entry["status_code"] == 200
    assert isinstance(entry["duration_ms"], float)
    assert entry["request_id"] == response.headers[REQUEST_ID_HEADER]


def test_request_bodies_are_not_logged(
    make_app: MakeApp, capsys: pytest.CaptureFixture[str]
) -> None:
    client = TestClient(make_app())
    capsys.readouterr()
    client.post("/api/v1/test/items", json={"name": "a", "password": "body-secret"})
    client.post("/api/v1/test/items", json={"password": "body-secret", "bad": 1})
    assert "body-secret" not in capsys.readouterr().out


def test_server_errors_are_logged_at_error_level_with_traceback(
    make_app: MakeApp, capsys: pytest.CaptureFixture[str]
) -> None:
    client = TestClient(make_app(), raise_server_exceptions=False)
    capsys.readouterr()
    response = client.get("/api/v1/test/crash")
    request_id = response.headers[REQUEST_ID_HEADER]

    entries = _json_lines(capsys.readouterr().out)
    [unhandled] = [e for e in entries if e.get("event") == "error.unhandled"]
    assert unhandled["level"] == "ERROR"
    assert unhandled["request_id"] == request_id
    assert unhandled["exception"]["type"] == "RuntimeError"
    assert "secret internal detail" in unhandled["exception"]["traceback"]
    [request] = [e for e in entries if e.get("event") == "http.request"]
    assert request["level"] == "ERROR"
    assert request["status_code"] == 500
    assert request["request_id"] == request_id


def test_safe_client_request_id_is_reused(make_app: MakeApp) -> None:
    response = TestClient(make_app()).get(
        "/api/v1/nothing", headers={REQUEST_ID_HEADER: "client-abc-123"}
    )
    assert response.headers[REQUEST_ID_HEADER] == "client-abc-123"
    assert response.json()["error"]["request_id"] == "client-abc-123"


@pytest.mark.parametrize("unsafe", ["short", "x" * 65, "has spaces in it", "inject}{\"a\":1"])
def test_unsafe_client_request_id_is_replaced(make_app: MakeApp, unsafe: str) -> None:
    response = TestClient(make_app()).get("/api/v1/nothing", headers={REQUEST_ID_HEADER: unsafe})
    generated = response.headers[REQUEST_ID_HEADER]
    assert generated != unsafe
    assert len(generated) == 32 and all(c in "0123456789abcdef" for c in generated)
