import hashlib
import re
from collections.abc import Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from helpers import AegisTestClient

from app.core.config import Environment, Settings
from app.main import API_DOCS_PATH, OPENAPI_PATH, SWAGGER_ASSETS_DIR, SWAGGER_ASSETS_PATH
from app.services import accounts

MakeApp = Callable[..., FastAPI]
PASSWORD = "correct horse battery staple"


def test_documentation_is_disabled_in_production_by_default(make_app: MakeApp) -> None:
    client = TestClient(make_app(Settings()))
    assert client.get(OPENAPI_PATH).status_code == 404
    assert client.get(API_DOCS_PATH).status_code == 404


def _admin_client(app: FastAPI, *, admin: bool = True) -> AegisTestClient:
    with app.state.database.session() as db:
        accounts.create_account(
            db,
            email="docs@example.com",
            username="docsreader",
            password=PASSWORD,
            instance_admin=admin,
        )
    client = AegisTestClient(app)
    response = client.post(
        "/api/v1/auth/login", json={"email": "docs@example.com", "password": PASSWORD}
    )
    assert response.status_code == 200
    return client


@pytest.mark.parametrize("path", [OPENAPI_PATH, API_DOCS_PATH])
def test_documentation_is_never_public(auth_app: FastAPI, path: str) -> None:
    """The schema maps every endpoint; anonymous visitors get 401, not the map."""
    response = AegisTestClient(auth_app).get(path)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_required"
    assert "paths" not in response.text


@pytest.mark.parametrize("path", [OPENAPI_PATH, API_DOCS_PATH])
def test_documentation_requires_an_instance_administrator(auth_app: FastAPI, path: str) -> None:
    response = _admin_client(auth_app, admin=False).get(path)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_instance_administrators_can_read_the_documentation(auth_app: FastAPI) -> None:
    client = _admin_client(auth_app)
    schema = client.get(OPENAPI_PATH)
    assert schema.status_code == 200
    assert schema.headers["cache-control"] == "no-store"
    assert "/api/v1/auth/login" in schema.json()["paths"]
    docs = client.get(API_DOCS_PATH)
    assert docs.status_code == 200
    assert docs.headers["cache-control"] == "no-store"
    assert "swagger-ui" in docs.text.lower()


def test_documentation_can_be_enabled_explicitly_in_production(make_app: MakeApp) -> None:
    client = TestClient(make_app(Settings(api_docs_enabled=True)))
    # Enabled, but still not public.
    assert client.get(OPENAPI_PATH).status_code != 404


def test_documentation_can_be_disabled_explicitly_in_development(make_app: MakeApp) -> None:
    client = TestClient(
        make_app(Settings(environment=Environment.DEVELOPMENT, api_docs_enabled=False))
    )
    assert client.get(OPENAPI_PATH).status_code == 404
    assert client.get(API_DOCS_PATH).status_code == 404


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json", "/api/redoc"])
def test_framework_default_documentation_paths_are_never_served(
    make_app: MakeApp, path: str
) -> None:
    client = TestClient(make_app(Settings(environment=Environment.DEVELOPMENT)))
    assert client.get(path).status_code == 404


def test_openapi_documents_the_standard_error_format(make_app: MakeApp) -> None:
    schema = make_app(Settings(environment=Environment.DEVELOPMENT)).openapi()

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


def test_documentation_page_uses_only_local_assets(auth_app: FastAPI) -> None:
    page = _admin_client(auth_app).get(API_DOCS_PATH)
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
