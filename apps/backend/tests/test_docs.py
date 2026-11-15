from collections.abc import Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Environment, Settings
from app.main import API_DOCS_PATH, OPENAPI_PATH

MakeApp = Callable[..., FastAPI]


def test_documentation_is_disabled_in_production_by_default(make_app: MakeApp) -> None:
    client = TestClient(make_app(Settings()))
    assert client.get(OPENAPI_PATH).status_code == 404
    assert client.get(API_DOCS_PATH).status_code == 404


@pytest.mark.parametrize("environment", [Environment.DEVELOPMENT, Environment.TEST])
def test_documentation_is_served_outside_production(
    make_app: MakeApp, environment: Environment
) -> None:
    client = TestClient(make_app(Settings(environment=environment)))
    assert client.get(OPENAPI_PATH).status_code == 200
    docs = client.get(API_DOCS_PATH)
    assert docs.status_code == 200
    assert "swagger-ui" in docs.text.lower()


def test_documentation_can_be_enabled_explicitly_in_production(make_app: MakeApp) -> None:
    client = TestClient(make_app(Settings(api_docs_enabled=True)))
    assert client.get(OPENAPI_PATH).status_code == 200


def test_documentation_can_be_disabled_explicitly_in_development(make_app: MakeApp) -> None:
    client = TestClient(
        make_app(Settings(environment=Environment.DEVELOPMENT, api_docs_enabled=False))
    )
    assert client.get(OPENAPI_PATH).status_code == 404


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json", "/api/redoc"])
def test_framework_default_documentation_paths_are_never_served(
    make_app: MakeApp, path: str
) -> None:
    client = TestClient(make_app(Settings(environment=Environment.DEVELOPMENT)))
    assert client.get(path).status_code == 404


def test_openapi_documents_the_standard_error_format(make_app: MakeApp) -> None:
    schema = TestClient(make_app(Settings(environment=Environment.DEVELOPMENT))).get(
        OPENAPI_PATH
    ).json()

    assert schema["info"]["title"] == "AEGIS API"
    assert schema["info"]["license"]["identifier"] == "Apache-2.0"
    assert "ErrorResponse" in schema["components"]["schemas"]
    assert "HTTPValidationError" not in schema["components"]["schemas"]

    operation = schema["paths"]["/api/v1/test/items"]["post"]
    for status in ("422", "500"):
        reference = operation["responses"][status]["content"]["application/json"]["schema"]
        assert reference["$ref"] == "#/components/schemas/ErrorResponse"
