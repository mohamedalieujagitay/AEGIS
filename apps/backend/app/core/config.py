"""Environment-based configuration.

Settings are read from environment variables prefixed with ``AEGIS_`` and,
for local development only, from an optional ``.env`` file in the working
directory. Environment variables take precedence over the file.

Defaults are secure: without configuration the application runs as
``production`` with debug mode off and API documentation disabled. Secrets
must never be given defaults here; they are added as required fields when
the features that use them are built.
"""

from enum import StrEnum
from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Deployment environment."""

    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]
LogFormat = Literal["json", "text"]
DatabaseSslMode = Literal["disable", "prefer", "require", "verify-ca", "verify-full"]

DEFAULT_MAX_REQUEST_BODY_BYTES = 1024 * 1024


class Settings(BaseSettings):
    """Application settings, validated at startup."""

    model_config = SettingsConfigDict(
        env_prefix="AEGIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    environment: Environment = Environment.PRODUCTION
    """Deployment environment. Defaults to production, the most restrictive."""

    debug: bool = False
    """Framework debug mode. Never allowed in production."""

    log_level: LogLevel = "INFO"
    """Minimum level for application logs."""

    log_format: LogFormat = "json"
    """``json`` (structured, one object per line) or ``text`` (readable, for local use)."""

    api_docs_enabled: bool | None = None
    """Serve OpenAPI and Swagger UI. Unset means enabled outside production only."""

    max_request_body_bytes: int = Field(default=DEFAULT_MAX_REQUEST_BODY_BYTES, gt=0)
    """Largest accepted request body. Larger requests are rejected with 413."""

    # PostgreSQL. The connection URL is built from these fields by
    # ``app.database.config.build_database_url``; it is never configured or
    # logged as a single string, so the password cannot leak through it.
    database_host: str | None = None
    """PostgreSQL host. Unset means no database is configured."""

    database_port: int = Field(default=5432, ge=1, le=65535)
    database_name: str = Field(default="aegis", min_length=1)
    database_user: str = Field(default="aegis", min_length=1)

    database_password: SecretStr | None = None
    """Database password. No default; required in production."""

    database_sslmode: DatabaseSslMode = "prefer"
    """libpq SSL mode. Use ``verify-full`` for databases reached over untrusted networks."""

    database_connect_timeout: int = Field(default=5, ge=1, le=60)
    """Seconds to wait for a new database connection before failing."""

    database_pool_size: int = Field(default=5, ge=1, le=100)
    database_max_overflow: int = Field(default=10, ge=0, le=100)
    database_pool_timeout: int = Field(default=30, ge=1, le=300)
    """Seconds to wait for a free pooled connection before failing."""

    database_pool_recycle: int = Field(default=1800, ge=60)
    """Seconds after which pooled connections are replaced."""

    @model_validator(mode="after")
    def _reject_debug_in_production(self) -> Self:
        if self.debug and self.environment is Environment.PRODUCTION:
            raise ValueError("debug mode must not be enabled in the production environment")
        return self

    @model_validator(mode="after")
    def _require_database_password_in_production(self) -> Self:
        if (
            self.environment is Environment.PRODUCTION
            and self.database_host is not None
            and (self.database_password is None or not self.database_password.get_secret_value())
        ):
            raise ValueError("a database password is required in the production environment")
        return self

    @property
    def database_configured(self) -> bool:
        """Whether a database connection has been configured."""
        return self.database_host is not None

    @property
    def docs_enabled(self) -> bool:
        """Whether API documentation is served, after applying the default."""
        if self.api_docs_enabled is not None:
            return self.api_docs_enabled
        return self.environment is not Environment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings, loaded once on first use."""
    return Settings()
