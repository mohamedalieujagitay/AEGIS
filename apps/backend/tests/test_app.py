import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from app import __version__
from app.api import v1
from app.api.router import API_V1_PREFIX, build_api_router
from app.api.v1 import account, admin, auth, health
from app.core.config import Environment, Settings
from app.main import create_app


def test_create_app_uses_project_metadata() -> None:
    app = create_app(Settings())
    assert app.title == "AEGIS API"
    assert app.version == __version__


def test_create_app_applies_settings() -> None:
    development = Settings(environment=Environment.DEVELOPMENT, debug=True)
    app = create_app(development)
    assert app.debug is True
    assert app.state.settings is development

    assert create_app(Settings()).debug is False


def test_create_app_reads_environment_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "test")
    assert create_app().state.settings.environment is Environment.TEST


def test_no_unversioned_root_endpoint() -> None:
    client = TestClient(create_app(Settings()))
    assert client.get("/").status_code == 404


def test_version_1_router_registry_contains_only_implemented_features() -> None:
    # Health checks (roadmap task 1.5), authentication (2.1), account management (2.2).
    assert [health.router, auth.router, account.router, admin.router] == v1.ROUTERS


def test_feature_routers_are_mounted_under_the_versioned_prefix() -> None:
    feature = APIRouter(prefix="/example")

    @feature.get("/ping")
    def ping() -> dict[str, str]:
        return {"pong": "ok"}

    app = create_app(Settings())
    app.router.routes.clear()
    app.include_router(build_api_router([feature]))
    client = TestClient(app)

    assert API_V1_PREFIX == "/api/v1"
    response = client.get("/api/v1/example/ping")
    assert response.status_code == 200
    assert response.json() == {"pong": "ok"}
    assert client.get("/example/ping").status_code == 404
    assert client.get("/api/v2/example/ping").status_code == 404
