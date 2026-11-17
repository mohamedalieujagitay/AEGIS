from collections.abc import Callable, Iterator

from fastapi import FastAPI
from helpers import AegisTestClient

from app.core.config import Settings
from app.core.request_context import REQUEST_ID_HEADER

MakeApp = Callable[..., FastAPI]

SECRET = "hunter2-do-not-echo"


def test_valid_request_is_accepted(make_app: MakeApp) -> None:
    response = AegisTestClient(make_app()).post(
        "/api/v1/test/items", json={"name": "  example.com  ", "password": SECRET}
    )
    assert response.status_code == 201
    assert response.json() == {"name": "example.com"}  # whitespace stripped


def test_unknown_fields_are_rejected(make_app: MakeApp) -> None:
    response = AegisTestClient(make_app()).post(
        "/api/v1/test/items", json={"name": "a", "password": SECRET, "admin": True}
    )
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["request_id"] == response.headers[REQUEST_ID_HEADER]
    assert {
        "location": ["body", "admin"],
        "message": "Extra inputs are not permitted",
        "type": "extra_forbidden",
    } in error["details"]


def test_missing_and_invalid_fields_are_reported_with_locations(make_app: MakeApp) -> None:
    response = AegisTestClient(make_app()).post("/api/v1/test/items", json={"name": ""})
    assert response.status_code == 422
    locations = {tuple(d["location"]) for d in response.json()["error"]["details"]}
    assert ("body", "name") in locations
    assert ("body", "password") in locations


def test_validation_errors_never_echo_submitted_values(make_app: MakeApp) -> None:
    response = AegisTestClient(make_app()).post(
        "/api/v1/test/items", json={"name": "x" * 60, "password": SECRET, "extra": SECRET}
    )
    assert response.status_code == 422
    assert SECRET not in response.text
    assert "x" * 60 not in response.text
    for detail in response.json()["error"]["details"]:
        assert set(detail) == {"location", "message", "type"}


def test_invalid_query_parameter(make_app: MakeApp) -> None:
    response = AegisTestClient(make_app()).get("/api/v1/test/items", params={"page": "zero"})
    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["location"] == ["query", "page"]


def test_malformed_json_is_a_validation_error(make_app: MakeApp) -> None:
    response = AegisTestClient(make_app()).post(
        "/api/v1/test/items",
        content=b'{"name": "a", "password": ',
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_body_over_declared_limit_is_rejected(make_app: MakeApp) -> None:
    client = AegisTestClient(make_app(Settings(max_request_body_bytes=64)))
    response = client.post("/api/v1/test/items", json={"name": "a", "password": "p" * 100})
    assert response.status_code == 413
    error = response.json()["error"]
    assert error["code"] == "request_too_large"
    assert error["request_id"] == response.headers[REQUEST_ID_HEADER]


def test_streamed_body_over_limit_is_rejected(make_app: MakeApp) -> None:
    def chunks() -> Iterator[bytes]:
        yield b'{"name": "a", "password": "'
        yield b"p" * 100
        yield b'"}'

    client = AegisTestClient(make_app(Settings(max_request_body_bytes=64)))
    response = client.post(
        "/api/v1/test/items", content=chunks(), headers={"content-type": "application/json"}
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "request_too_large"


def test_body_within_limit_is_accepted(make_app: MakeApp) -> None:
    client = AegisTestClient(make_app(Settings(max_request_body_bytes=64)))
    response = client.post("/api/v1/test/items", json={"name": "a", "password": "p"})
    assert response.status_code == 201
