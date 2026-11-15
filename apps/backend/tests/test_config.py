from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import DEFAULT_MAX_REQUEST_BODY_BYTES, Environment, Settings, get_settings


def test_defaults_are_secure() -> None:
    settings = Settings()
    assert settings.environment is Environment.PRODUCTION
    assert settings.debug is False
    assert settings.docs_enabled is False
    assert settings.log_level == "INFO"
    assert settings.log_format == "json"
    assert settings.max_request_body_bytes == DEFAULT_MAX_REQUEST_BODY_BYTES


def test_reads_prefixed_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    monkeypatch.setenv("AEGIS_DEBUG", "true")
    monkeypatch.setenv("AEGIS_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("AEGIS_LOG_FORMAT", "text")
    monkeypatch.setenv("AEGIS_MAX_REQUEST_BODY_BYTES", "2048")
    settings = Settings()
    assert settings.environment is Environment.DEVELOPMENT
    assert settings.debug is True
    assert settings.log_level == "DEBUG"
    assert settings.log_format == "text"
    assert settings.max_request_body_bytes == 2048


def test_ignores_unprefixed_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("DEBUG", "true")
    settings = Settings()
    assert settings.environment is Environment.PRODUCTION
    assert settings.debug is False


def test_reads_dotenv_file_and_environment_takes_precedence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    Path(".env").write_text("AEGIS_ENVIRONMENT=test\nAEGIS_DEBUG=true\n", encoding="utf-8")
    assert Settings().environment is Environment.TEST

    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    assert Settings().environment is Environment.DEVELOPMENT


def test_rejects_debug_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AEGIS_DEBUG", "true")
    with pytest.raises(ValidationError, match="debug mode must not be enabled"):
        Settings()


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("AEGIS_ENVIRONMENT", "staging"),
        ("AEGIS_DEBUG", "sometimes"),
        ("AEGIS_LOG_LEVEL", "VERBOSE"),
        ("AEGIS_LOG_FORMAT", "xml"),
        ("AEGIS_MAX_REQUEST_BODY_BYTES", "0"),
        ("AEGIS_MAX_REQUEST_BODY_BYTES", "-1"),
        ("AEGIS_API_DOCS_ENABLED", "maybe"),
    ],
)
def test_rejects_invalid_values(monkeypatch: pytest.MonkeyPatch, name: str, value: str) -> None:
    monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize(
    ("environment", "explicit", "expected"),
    [
        (Environment.PRODUCTION, None, False),
        (Environment.DEVELOPMENT, None, True),
        (Environment.TEST, None, True),
        (Environment.PRODUCTION, True, True),
        (Environment.DEVELOPMENT, False, False),
    ],
)
def test_docs_enabled_default_depends_on_environment(
    environment: Environment, explicit: bool | None, expected: bool
) -> None:
    settings = Settings(environment=environment, api_docs_enabled=explicit)
    assert settings.docs_enabled is expected


def test_settings_are_immutable() -> None:
    settings = Settings()
    with pytest.raises(ValidationError):
        setattr(settings, "debug", True)


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()
