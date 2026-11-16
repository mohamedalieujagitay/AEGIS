import hashlib
import re
from collections.abc import Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Environment, Settings
from app.main import API_DOCS_PATH, OPENAPI_PATH, SWAGGER_ASSETS_DIR, SWAGGER_ASSETS_PATH

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
    schema = (
        TestClient(make_app(Settings(environment=Environment.DEVELOPMENT))).get(OPENAPI_PATH).json()
    )

    assert schema["info"]["title"] == "AEGIS API"
    assert schema["info"]["license"]["identifier"] == "Apache-2.0"
    assert "ErrorResponse" in schema["components"]["schemas"]
    assert "HTTPValidationError" not in schema["components"]["schemas"]

    operation = schema["paths"]["/api/v1/test/items"]["post"]
    for status in ("422", "500"):
        reference = operation["responses"][status]["content"]["application/json"]["schema"]
        assert reference["$ref"] == "#/components/schemas/ErrorResponse"


# --- Local Swagger UI assets (DECISIONS.md D-056) ---------------------------

SWAGGER_FILES = ("swagger-ui-bundle.js", "swagger-ui.css", "favicon-32x32.png")


def test_documentation_page_uses_only_local_assets(make_app: MakeApp) -> None:
    page = TestClient(make_app(Settings(environment=Environment.DEVELOPMENT))).get(API_DOCS_PATH)
    assert page.status_code == 200
    for name in SWAGGER_FILES:
        assert f"{SWAGGER_ASSETS_PATH}/{name}" in page.text
    for external in (
        "cdn.jsdelivr.net",
        "unpkg.com",
        "fastapi.tiangolo.com",
        "validator.swagger.io",
    ):
        assert external not in page.text
    # The public schema validator is disabled explicitly.
    assert '"validatorUrl": null' in page.text


@pytest.mark.parametrize("name", SWAGGER_FILES)
def test_swagger_assets_are_served_with_the_documentation(make_app: MakeApp, name: str) -> None:
    client = TestClient(make_app(Settings(environment=Environment.DEVELOPMENT)))
    response = client.get(f"{SWAGGER_ASSETS_PATH}/{name}")
    assert response.status_code == 200
    assert response.content == (SWAGGER_ASSETS_DIR / name).read_bytes()


def test_swagger_assets_are_not_served_when_documentation_is_disabled(make_app: MakeApp) -> None:
    client = TestClient(make_app(Settings()))
    assert client.get(f"{SWAGGER_ASSETS_PATH}/swagger-ui-bundle.js").status_code == 404


def test_vendored_swagger_files_match_their_recorded_hashes() -> None:
    provenance = (SWAGGER_ASSETS_DIR / "PROVENANCE.txt").read_text(encoding="utf-8")
    recorded: dict[str, str] = {}
    for line in provenance.splitlines():
        if re.match(r"^[0-9a-f]{64}  ", line):
            digest, name = line.split()
            recorded[name] = digest
    expected = {*SWAGGER_FILES, "LICENSE", "NOTICE", "swagger-ui-bundle.js.LICENSE.txt"}
    assert set(recorded) == expected
    for name, digest in recorded.items():
        assert hashlib.sha256((SWAGGER_ASSETS_DIR / name).read_bytes()).hexdigest() == digest
