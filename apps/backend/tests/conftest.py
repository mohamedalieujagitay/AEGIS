import os
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path

import psycopg
import pytest
from fastapi import APIRouter, FastAPI, Query
from postgres_harness import PostgresServer, find_postgres_bin, temporary_postgres
from psycopg import sql
from pydantic import Field

from app.api import v1
from app.core.config import Environment, Settings, get_settings
from app.core.errors import AppError
from app.main import create_app
from app.schemas.base import RequestModel


@pytest.fixture(autouse=True)
def _isolated_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """Give every test a clean configuration.

    Removes AEGIS_* variables from the environment, runs from an empty
    directory so a developer's local .env is never read, and clears the
    cached settings before and after the test.
    """
    for name in list(os.environ):
        if name.startswith("AEGIS_"):
            monkeypatch.delenv(name)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class ItemCreate(RequestModel):
    name: str = Field(min_length=1, max_length=50)
    password: str


class ItemNotFoundError(AppError):
    status_code = 404
    code = "item_not_found"
    message = "The item does not exist."


def _test_router() -> APIRouter:
    """Endpoints that exist only in tests, to exercise the shared behaviour."""
    router = APIRouter(prefix="/test")

    @router.post("/items", status_code=201)
    def create_item(item: ItemCreate) -> dict[str, str]:
        return {"name": item.name}

    @router.get("/items")
    def list_items(page: int = Query(ge=1)) -> dict[str, int]:
        return {"page": page}

    @router.get("/missing")
    def missing() -> None:
        raise ItemNotFoundError()

    @router.get("/crash")
    def crash() -> None:
        raise RuntimeError("secret internal detail")

    return router


@pytest.fixture
def make_app(monkeypatch: pytest.MonkeyPatch) -> Callable[..., FastAPI]:
    """Create the real application with the test-only router registered."""

    def factory(settings: Settings | None = None) -> FastAPI:
        monkeypatch.setattr(v1, "ROUTERS", [_test_router()])
        return create_app(settings if settings is not None else Settings())

    return factory


# Read once at import, before the autouse fixture above removes AEGIS_*
# variables from each test's environment. CI sets it to 1, so database tests
# fail instead of being skipped when PostgreSQL is missing.
REQUIRE_POSTGRES = os.environ.get("AEGIS_TEST_REQUIRE_POSTGRES") == "1"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark every test that uses the PostgreSQL server with ``database``."""
    for item in items:
        if "postgres_server" in getattr(item, "fixturenames", ()):
            item.add_marker(pytest.mark.database)


@pytest.fixture(scope="session")
def postgres_server(tmp_path_factory: pytest.TempPathFactory) -> Iterator[PostgresServer]:
    """A disposable PostgreSQL server for the whole test session."""
    bin_dir = find_postgres_bin()
    if bin_dir is None:
        message = "PostgreSQL binaries not found; set AEGIS_TEST_POSTGRES_BIN to run database tests"
        if REQUIRE_POSTGRES:
            pytest.fail(f"{message} (required because AEGIS_TEST_REQUIRE_POSTGRES=1)")
        pytest.skip(message)
    with temporary_postgres(bin_dir, tmp_path_factory.mktemp("postgres")) as server:
        yield server


def _admin_connection(server: PostgresServer) -> psycopg.Connection[tuple[object, ...]]:
    return psycopg.connect(
        host=server.host, port=server.port, user=server.user, dbname="postgres", autocommit=True
    )


@pytest.fixture
def database_settings(postgres_server: PostgresServer) -> Iterator[Settings]:
    """Settings pointing at a new, empty database that is dropped afterwards."""
    name = f"aegis_test_{uuid.uuid4().hex[:12]}"
    with _admin_connection(postgres_server) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    try:
        yield Settings(
            environment=Environment.TEST,
            database_host=postgres_server.host,
            database_port=postgres_server.port,
            database_user=postgres_server.user,
            database_name=name,
            database_sslmode="disable",
        )
    finally:
        with _admin_connection(postgres_server) as connection:
            connection.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name))
            )
