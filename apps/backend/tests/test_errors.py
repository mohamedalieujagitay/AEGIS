import logging
from collections.abc import Callable

import pytest
from fastapi import FastAPI
from helpers import AegisTestClient

from app.core.errors import AppError
from app.core.request_context import REQUEST_ID_HEADER

MakeApp = Callable[..., FastAPI]


def _assert_error_envelope(body: dict[str, object], code: str, request_id: str) -> None:
    error = body["error"]
    assert isinstance(error, dict)
    assert error["code"] == code
    assert isinstance(error["message"], str)
    assert error["message"]
    assert error["request_id"] == request_id


def test_unknown_route_returns_standard_404(make_app: MakeApp) -> None:
    response = AegisTestClient(make_app()).get("/api/v1/nothing-here")
    assert response.status_code == 404
    _assert_error_envelope(response.json(), "not_found", response.headers[REQUEST_ID_HEADER])
    assert response.json()["error"]["message"] == "Not Found."


def test_wrong_method_returns_405_with_allow_header(make_app: MakeApp) -> None:
    response = AegisTestClient(make_app()).delete("/api/v1/test/items")
    assert response.status_code == 405
    _assert_error_envelope(
        response.json(), "method_not_allowed", response.headers[REQUEST_ID_HEADER]
    )
    # Starlette lists the methods of the first route matching the path.
    assert response.headers["allow"]


def test_application_error_uses_its_status_code_and_message(make_app: MakeApp) -> None:
    response = AegisTestClient(make_app()).get("/api/v1/test/missing")
    assert response.status_code == 404
    _assert_error_envelope(response.json(), "item_not_found", response.headers[REQUEST_ID_HEADER])
    assert response.json()["error"]["message"] == "The item does not exist."


def test_app_error_message_can_be_overridden() -> None:
    assert AppError().message == "The request could not be processed."
    assert AppError("Custom safe message.").message == "Custom safe message."


def test_unexpected_error_hides_internal_details(
    make_app: MakeApp, caplog: pytest.LogCaptureFixture
) -> None:
    client = AegisTestClient(make_app(), raise_server_exceptions=False)
    with caplog.at_level(logging.INFO):
        response = client.get("/api/v1/test/crash")

    assert response.status_code == 500
    request_id = response.headers[REQUEST_ID_HEADER]
    _assert_error_envelope(response.json(), "internal_error", request_id)
    assert "secret internal detail" not in response.text
    assert "RuntimeError" not in response.text
    assert "Traceback" not in response.text

    # The full exception is logged server-side, with the request ID.
    errors = [r for r in caplog.records if r.name == "app.errors"]
    assert len(errors) == 1
    assert errors[0].levelno == logging.ERROR
    assert errors[0].exc_info is not None
    assert getattr(errors[0], "request_id", None) == request_id


def test_error_responses_omit_empty_details(make_app: MakeApp) -> None:
    body = AegisTestClient(make_app()).get("/api/v1/nothing-here").json()
    assert "details" not in body["error"]
