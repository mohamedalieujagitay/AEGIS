"""Valkey connection settings, broker client and secret files."""

import logging
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest
import redis
from pydantic import SecretStr, ValidationError

from app.broker.client import Broker
from app.broker.config import BrokerUnavailableError, build_broker_url, redis_client_options
from app.core.config import Environment, Settings, get_settings

PASSWORD = "p@ss:w/rd?#%"


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "environment": Environment.TEST,
        "valkey_host": "valkey",
        "valkey_username": "aegis-api",
        "valkey_password": SecretStr(PASSWORD),
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


# --- Settings ---------------------------------------------------------------


def test_broker_is_not_configured_by_default() -> None:
    settings = Settings()
    assert settings.valkey_configured is False
    assert (settings.valkey_port, settings.valkey_db, settings.valkey_tls) == (6379, 0, False)
    with pytest.raises(BrokerUnavailableError):
        build_broker_url(settings)


def test_production_requires_valkey_credentials() -> None:
    with pytest.raises(ValidationError, match="Valkey username and password"):
        Settings(valkey_host="valkey")
    with pytest.raises(ValidationError, match="Valkey username and password"):
        Settings(valkey_host="valkey", valkey_username="aegis-api", valkey_password=SecretStr(""))
    Settings(valkey_host="valkey", valkey_username="aegis-api", valkey_password=SecretStr("x"))


def test_task_time_limit_must_exceed_soft_limit() -> None:
    with pytest.raises(ValidationError, match="time limit must be greater"):
        Settings(worker_task_soft_time_limit=60, worker_task_time_limit=60)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("AEGIS_VALKEY_PORT", "0"),
        ("AEGIS_VALKEY_DB", "16"),
        ("AEGIS_VALKEY_USERNAME", ""),
        ("AEGIS_VALKEY_CONNECT_TIMEOUT", "0"),
        ("AEGIS_HEALTH_CHECK_TIMEOUT", "30"),
    ],
)
def test_rejects_invalid_broker_settings(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError):
        Settings()


# --- URL and client options -----------------------------------------------


def test_broker_url_escapes_credentials() -> None:
    url = build_broker_url(_settings())
    parts = urlsplit(url)
    assert parts.scheme == "redis"
    assert (parts.hostname, parts.port, parts.path) == ("valkey", 6379, "/0")
    assert unquote(parts.username or "") == "aegis-api"
    assert unquote(parts.password or "") == PASSWORD
    assert PASSWORD not in url  # only the encoded form appears


def test_broker_url_uses_tls_when_enabled() -> None:
    url = build_broker_url(_settings(valkey_tls=True, valkey_db=2))
    assert url.startswith("rediss://")
    assert url.endswith("/2?ssl_cert_reqs=required")


def test_broker_url_brackets_ipv6_hosts() -> None:
    assert "@[fd00::5]:6379/0" in build_broker_url(_settings(valkey_host="fd00::5"))


def test_client_options_match_the_settings() -> None:
    options = redis_client_options(
        _settings(valkey_connect_timeout=1.5, valkey_socket_timeout=4), "aegis-api"
    )
    assert options["host"] == "valkey"
    assert options["username"] == "aegis-api"
    assert options["password"] == PASSWORD
    assert options["socket_connect_timeout"] == 1.5
    assert options["socket_timeout"] == 4
    assert options["client_name"] == "aegis-api"


# --- Broker lifecycle ---------------------------------------------------------


def test_client_is_created_lazily_and_disposed() -> None:
    broker = Broker(_settings())
    assert broker._client is None
    client = broker.client
    assert broker.client is client
    assert client.connection_pool.max_connections == 4
    assert client.connection_pool.connection_class is redis.Connection
    assert "ssl_cert_reqs" not in client.connection_pool.connection_kwargs
    broker.dispose()
    assert broker._client is None
    broker.dispose()  # safe to call twice


def test_tls_client_uses_verified_tls_connections() -> None:
    broker = Broker(_settings(valkey_tls=True))
    pool = broker.client.connection_pool
    assert pool.connection_class is redis.SSLConnection
    assert pool.connection_kwargs["ssl_cert_reqs"] == "required"
    broker.dispose()


def test_unconfigured_broker_cannot_create_a_client() -> None:
    broker = Broker(Settings())
    assert broker.configured is False
    with pytest.raises(BrokerUnavailableError):
        broker.ping()


def test_ping_fails_cleanly_when_the_broker_is_unreachable() -> None:
    broker = Broker(_settings(valkey_host="127.0.0.1", valkey_port=1, valkey_connect_timeout=1))
    # Refused on Linux; Windows may time out instead. Both are clean failures.
    with pytest.raises((redis.ConnectionError, redis.TimeoutError)):
        broker.ping()
    broker.dispose()


def test_client_creation_log_never_contains_credentials(caplog: pytest.LogCaptureFixture) -> None:
    broker = Broker(_settings(valkey_username="secret-user"))
    with caplog.at_level(logging.INFO, logger="app.broker"):
        _ = broker.client
    broker.dispose()
    [record] = [r for r in caplog.records if getattr(r, "event", None) == "broker.client_created"]
    logged = str(record.__dict__)
    assert PASSWORD not in logged
    assert "secret-user" not in logged
    assert record.__dict__["broker_host"] == "valkey"


# --- Secret files (Docker secrets) ------------------------------------------


def _write_secret(directory: Path, name: str, value: str) -> None:
    (directory / name).write_text(value, encoding="utf-8")


def test_secrets_are_read_from_the_configured_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    _write_secret(secrets, "aegis_database_password", "db-secret")
    _write_secret(secrets, "aegis_valkey_password", "valkey-secret")
    monkeypatch.setenv("AEGIS_SECRETS_DIR", str(secrets))
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "test")

    settings = get_settings()
    assert settings.database_password is not None
    assert settings.database_password.get_secret_value() == "db-secret"
    assert settings.valkey_password is not None
    assert settings.valkey_password.get_secret_value() == "valkey-secret"
    assert "valkey-secret" not in repr(settings)


def test_environment_variables_take_precedence_over_secret_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write_secret(tmp_path, "aegis_valkey_password", "from-file")
    monkeypatch.setenv("AEGIS_SECRETS_DIR", str(tmp_path))
    monkeypatch.setenv("AEGIS_VALKEY_PASSWORD", "from-env")
    settings = get_settings()
    assert settings.valkey_password is not None
    assert settings.valkey_password.get_secret_value() == "from-env"


def test_secret_files_are_ignored_unless_a_directory_is_configured(tmp_path: Path) -> None:
    # The autouse fixture runs each test in an empty working directory.
    _write_secret(tmp_path, "aegis_valkey_password", "should-not-be-read")
    assert get_settings().valkey_password is None
