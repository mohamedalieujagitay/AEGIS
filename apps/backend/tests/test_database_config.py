"""Database configuration and engine tests. No database server is needed."""

import logging

import pytest
from pydantic import SecretStr, ValidationError
from sqlalchemy.pool import QueuePool

from app.core.config import Environment, Settings
from app.database.config import DRIVER, DatabaseUnavailableError, build_database_url
from app.database.engine import create_database_engine
from app.database.session import Database

PASSWORD = "p@ss:w/rd?#%"


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "environment": Environment.TEST,
        "database_host": "db.internal",
        "database_password": SecretStr(PASSWORD),
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def test_database_is_not_configured_by_default() -> None:
    settings = Settings()
    assert settings.database_configured is False
    assert settings.database_port == 5432
    assert settings.database_sslmode == "prefer"
    with pytest.raises(DatabaseUnavailableError):
        build_database_url(settings)


def test_reads_database_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in {
        "AEGIS_ENVIRONMENT": "test",
        "AEGIS_DATABASE_HOST": "postgres",
        "AEGIS_DATABASE_PORT": "6543",
        "AEGIS_DATABASE_NAME": "aegis_dev",
        "AEGIS_DATABASE_USER": "aegis_app",
        "AEGIS_DATABASE_PASSWORD": "from-env",
        "AEGIS_DATABASE_SSLMODE": "verify-full",
        "AEGIS_DATABASE_POOL_SIZE": "8",
    }.items():
        monkeypatch.setenv(name, value)
    settings = Settings()
    assert settings.database_configured is True
    url = build_database_url(settings)
    assert (url.host, url.port, url.database, url.username) == (
        "postgres", 6543, "aegis_dev", "aegis_app"
    )
    assert url.password == "from-env"
    assert url.query["sslmode"] == "verify-full"
    assert settings.database_pool_size == 8


def test_url_uses_psycopg_driver_and_connection_options() -> None:
    url = build_database_url(_settings(database_connect_timeout=7))
    assert url.drivername == DRIVER == "postgresql+psycopg"
    assert url.query["connect_timeout"] == "7"
    assert url.query["application_name"] == "aegis-api"


def test_special_characters_in_password_are_preserved() -> None:
    url = build_database_url(_settings())
    assert url.password == PASSWORD


def test_password_never_appears_when_url_or_settings_are_printed() -> None:
    settings = _settings()
    url = build_database_url(settings)
    for text in (str(url), repr(url), repr(settings), str(settings.model_dump())):
        assert PASSWORD not in text
    assert "***" in str(url)


def test_production_requires_a_database_password() -> None:
    with pytest.raises(ValidationError, match="database password is required"):
        Settings(database_host="db.internal")
    with pytest.raises(ValidationError, match="database password is required"):
        Settings(database_host="db.internal", database_password=SecretStr(""))
    Settings(database_host="db.internal", database_password=SecretStr("set"))


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("AEGIS_DATABASE_PORT", "0"),
        ("AEGIS_DATABASE_PORT", "70000"),
        ("AEGIS_DATABASE_SSLMODE", "allow-anything"),
        ("AEGIS_DATABASE_POOL_SIZE", "0"),
        ("AEGIS_DATABASE_CONNECT_TIMEOUT", "0"),
        ("AEGIS_DATABASE_NAME", ""),
    ],
)
def test_rejects_invalid_database_settings(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError):
        Settings()


def test_engine_applies_pool_settings_and_hides_parameters() -> None:
    engine = create_database_engine(
        _settings(database_pool_size=3, database_max_overflow=2, database_pool_timeout=9)
    )
    try:
        pool = engine.pool
        assert isinstance(pool, QueuePool)
        assert pool.size() == 3
        assert pool._max_overflow == 2
        assert pool._timeout == 9
        assert pool._pre_ping is True
        assert engine.hide_parameters is True
        assert engine.echo is False
    finally:
        engine.dispose()


def test_creating_the_engine_does_not_connect() -> None:
    # Port 1 on localhost refuses connections; creating the engine must not try.
    database = Database(_settings(database_host="127.0.0.1", database_port=1))
    pool = database.engine.pool
    assert isinstance(pool, QueuePool)
    assert pool.checkedout() == 0
    database.dispose()


def test_engine_is_created_lazily_and_disposed() -> None:
    database = Database(_settings())
    assert database._engine is None
    first = database.engine
    assert database.engine is first
    database.dispose()
    assert database._engine is None
    database.dispose()  # safe to call twice


def test_unconfigured_database_cannot_create_an_engine() -> None:
    database = Database(Settings())
    assert database.configured is False
    with pytest.raises(DatabaseUnavailableError):
        _ = database.engine
    database.dispose()


def test_engine_creation_log_never_contains_credentials(
    caplog: pytest.LogCaptureFixture,
) -> None:
    database = Database(_settings(database_user="secret_user"))
    with caplog.at_level(logging.INFO, logger="app.database"):
        _ = database.engine
    database.dispose()
    [record] = [r for r in caplog.records if getattr(r, "event", None) == "database.engine_created"]
    assert getattr(record, "db_host") == "db.internal"
    logged = str(record.__dict__)
    assert PASSWORD not in logged
    assert "secret_user" not in logged
