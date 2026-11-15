"""Connection and session management tests against a disposable PostgreSQL."""

from collections.abc import Callable

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api import v1
from app.core.config import Environment, Settings
from app.core.request_context import REQUEST_ID_HEADER
from app.database.session import Database, get_db_session
from app.main import create_app


def test_ping_connects_to_the_database(database_settings: Settings) -> None:
    database = Database(database_settings)
    try:
        database.ping()
        with database.engine.connect() as connection:
            name = connection.execute(text("SELECT current_database()")).scalar_one()
            application = connection.execute(
                text("SELECT current_setting('application_name')")
            ).scalar_one()
        assert name == database_settings.database_name
        assert application == "aegis-api"
    finally:
        database.dispose()


def test_session_commits_on_success_and_rolls_back_on_error(
    database_settings: Settings,
) -> None:
    database = Database(database_settings)
    try:
        with database.session() as session:
            session.execute(text("CREATE TABLE notes (body text NOT NULL)"))
            session.execute(text("INSERT INTO notes (body) VALUES (:body)"), {"body": "kept"})

        with pytest.raises(RuntimeError), database.session() as session:
            session.execute(text("INSERT INTO notes (body) VALUES (:body)"), {"body": "discarded"})
            raise RuntimeError("abort")

        with database.session() as session:
            rows = session.execute(text("SELECT body FROM notes")).scalars().all()
        assert rows == ["kept"]
    finally:
        database.dispose()


def test_bound_parameters_are_not_interpreted_as_sql(database_settings: Settings) -> None:
    database = Database(database_settings)
    hostile = "x'); DROP TABLE notes; --"
    try:
        with database.session() as session:
            session.execute(text("CREATE TABLE notes (body text NOT NULL)"))
            session.execute(text("INSERT INTO notes (body) VALUES (:body)"), {"body": hostile})
        with database.session() as session:
            assert session.execute(text("SELECT body FROM notes")).scalar_one() == hostile
    finally:
        database.dispose()


def test_ping_fails_cleanly_when_the_database_is_unreachable() -> None:
    database = Database(
        Settings(
            environment=Environment.TEST,
            database_host="127.0.0.1",
            database_port=1,
            database_password=SecretStr("never-shown"),
            database_connect_timeout=2,
            database_sslmode="disable",
        )
    )
    try:
        with pytest.raises(OperationalError) as caught:
            database.ping()
        assert "never-shown" not in str(caught.value)
    finally:
        database.dispose()


def _session_router() -> APIRouter:
    router = APIRouter(prefix="/db")

    @router.post("/notes", status_code=201)
    def add_note(session: Session = Depends(get_db_session)) -> dict[str, int]:
        session.execute(text("CREATE TABLE IF NOT EXISTS notes (body text NOT NULL)"))
        session.execute(text("INSERT INTO notes (body) VALUES ('from request')"))
        count = session.execute(text("SELECT count(*) FROM notes")).scalar_one()
        return {"count": int(count)}

    @router.post("/fail")
    def fail(session: Session = Depends(get_db_session)) -> None:
        session.execute(text("CREATE TABLE IF NOT EXISTS notes (body text NOT NULL)"))
        session.execute(text("INSERT INTO notes (body) VALUES ('rolled back')"))
        raise RuntimeError("handler failed")

    @router.get("/count")
    def count(session: Session = Depends(get_db_session)) -> dict[str, int]:
        result = session.execute(text("SELECT count(*) FROM notes")).scalar_one()
        return {"count": int(result)}

    return router


@pytest.fixture
def make_db_app(monkeypatch: pytest.MonkeyPatch) -> Callable[[Settings], FastAPI]:
    def factory(settings: Settings) -> FastAPI:
        monkeypatch.setattr(v1, "ROUTERS", [_session_router()])
        return create_app(settings)

    return factory


def test_request_session_commits_and_rolls_back(
    database_settings: Settings, make_db_app: Callable[[Settings], FastAPI]
) -> None:
    app = make_db_app(database_settings)
    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.post("/api/v1/db/notes").json() == {"count": 1}
        assert client.post("/api/v1/db/fail").status_code == 500
        assert client.get("/api/v1/db/count").json() == {"count": 1}


def test_application_does_not_connect_at_startup_and_disposes_on_shutdown(
    database_settings: Settings, make_db_app: Callable[[Settings], FastAPI]
) -> None:
    app = make_db_app(database_settings)
    database: Database = app.state.database
    with TestClient(app) as client:
        assert database._engine is None  # nothing connected at startup
        client.post("/api/v1/db/notes")
        assert database._engine is not None
    assert database._engine is None  # pool disposed on shutdown


@pytest.mark.parametrize("configured", [True, False])
def test_unavailable_database_returns_safe_503(
    make_db_app: Callable[[Settings], FastAPI], configured: bool
) -> None:
    settings = (
        Settings(
            environment=Environment.TEST,
            database_host="127.0.0.1",
            database_port=1,
            database_user="hidden_user",
            database_password=SecretStr("hidden-password"),
            database_connect_timeout=2,
            database_sslmode="disable",
        )
        if configured
        else Settings(environment=Environment.TEST)
    )
    with TestClient(make_db_app(settings)) as client:
        response = client.get("/api/v1/db/count")

    assert response.status_code == 503
    error = response.json()["error"]
    assert error["code"] == "database_unavailable"
    assert error["request_id"] == response.headers[REQUEST_ID_HEADER]
    for leaked in ("127.0.0.1", "hidden_user", "hidden-password", "psycopg", "connection"):
        assert leaked not in response.text
