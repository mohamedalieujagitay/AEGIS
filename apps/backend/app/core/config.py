"""Environment-based configuration.

Settings are read from environment variables prefixed with ``AEGIS_`` and,
for local development only, from an optional ``.env`` file in the working
directory. Environment variables take precedence over the file.

Defaults are secure: without configuration the application runs as
``production`` with debug mode off and API documentation disabled. Secrets
must never be given defaults here; they are added as required fields when
the features that use them are built.

Secrets can also be read from files (Docker secrets): when
``AEGIS_SECRETS_DIR`` is set, a file in that directory named after the
variable in lower case (for example ``aegis_database_password``) supplies
the value. Environment variables take precedence over secret files.
"""

import os
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

SECRETS_DIR_VARIABLE = "AEGIS_SECRETS_DIR"
"""Environment variable naming the directory that holds secret files."""


class Settings(BaseSettings):
    """Application settings, validated at startup."""

    model_config = SettingsConfigDict(
        env_prefix="AEGIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
        # Validation errors must not quote the input: it contains secrets.
        hide_input_in_errors=True,
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

    # Valkey, the Celery message broker (DECISIONS.md D-009). Each process
    # connects as its own ACL user, so the username and password differ per
    # role (API, internal worker, assessment worker).
    valkey_host: str | None = None
    """Valkey host. Unset means no broker is configured."""

    valkey_port: int = Field(default=6379, ge=1, le=65535)
    valkey_db: int = Field(default=0, ge=0, le=15)
    valkey_username: str | None = Field(default=None, min_length=1)
    """ACL user for this process."""

    valkey_password: SecretStr | None = None
    """Password of the ACL user. No default; required in production."""

    valkey_tls: bool = False
    """Connect with TLS (``rediss://``). Use when Valkey is reached over an untrusted network."""

    valkey_connect_timeout: float = Field(default=3.0, gt=0, le=60)
    """Seconds to wait for a new broker connection."""

    valkey_socket_timeout: float = Field(default=5.0, gt=0, le=60)
    """Seconds to wait for a broker reply."""

    health_check_timeout: float = Field(default=2.0, gt=0, le=10)
    """Seconds each readiness check may take before the dependency counts as unavailable."""

    worker_task_soft_time_limit: int = Field(default=300, ge=1)
    """Seconds after which a task is asked to stop (Celery soft time limit)."""

    worker_task_time_limit: int = Field(default=360, ge=1)
    """Seconds after which a task is terminated (Celery hard time limit)."""

    worker_heartbeat_file: str = "/tmp/aegis-worker-heartbeat"  # noqa: S108
    """File a worker touches while connected to the broker; read by its health check."""

    # Authentication (DECISIONS.md D-061 to D-068).
    secret_key: SecretStr | None = None
    """Server secret for CSRF tokens and rate-limit keys (at least 32 characters).
    Required by the API in production; read from the ``aegis_secret_key`` secret file."""

    allowed_origins: str = ""
    """Comma-separated browser origins allowed to send state-changing requests,
    for example ``https://aegis.example.com``. A request's own origin is always allowed."""

    cookie_secure: bool = True
    """Mark cookies ``Secure`` and use the ``__Host-`` prefix. Never disable in production."""

    session_idle_timeout_minutes: int = Field(default=60, ge=5, le=1440)
    """A session ends after this long without a request."""

    session_absolute_timeout_hours: int = Field(default=12, ge=1, le=168)
    """A session ends this long after sign-in, regardless of activity."""

    password_reset_token_ttl_minutes: int = Field(default=60, ge=5, le=1440)
    """How long a password reset token issued by an administrator stays valid."""

    password_hash_concurrency: int = Field(default=4, ge=1, le=32)
    """Argon2id hashes computed at the same time (each uses 64 MiB of memory)."""

    device_trust_days: int = Field(default=30, ge=1, le=30)
    """How long a browser that signed in with the password skips the per-account sign-in delay."""

    rate_limit_window_seconds: int = Field(default=900, ge=60, le=86400)
    """Window for the failure counters of the rate limits."""

    login_ip_max_failures: int = Field(default=30, ge=1)
    """Failed sign-ins per client address and window before the address is throttled."""

    login_pair_free_failures: int = Field(default=5, ge=1)
    """Failed sign-ins for one account from one address before progressive delays start."""

    login_account_throttle_failures: int = Field(default=20, ge=1)
    """Failed sign-ins for one account from any address before the account-wide delay."""

    login_account_delay_seconds: int = Field(default=10, ge=1, le=300)
    """Minimum interval between attempts on an account once it is being attacked."""

    registration_ip_max_attempts: int = Field(default=5, ge=1)
    """Registrations per client address and hour."""

    password_reset_ip_max_attempts: int = Field(default=10, ge=1)
    """Password reset attempts per client address and window."""

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

    @model_validator(mode="after")
    def _require_valkey_credentials_in_production(self) -> Self:
        if (
            self.environment is Environment.PRODUCTION
            and self.valkey_host is not None
            and (
                self.valkey_username is None
                or self.valkey_password is None
                or not self.valkey_password.get_secret_value()
            )
        ):
            raise ValueError("a Valkey username and password are required in production")
        return self

    @model_validator(mode="after")
    def _secure_authentication_settings(self) -> Self:
        if self.secret_key is not None and len(self.secret_key.get_secret_value()) < 32:
            raise ValueError("the secret key must be at least 32 characters long")
        if self.environment is Environment.PRODUCTION and not self.cookie_secure:
            raise ValueError("AEGIS_COOKIE_SECURE must be true in the production environment")
        return self

    @model_validator(mode="after")
    def _hard_limit_after_soft_limit(self) -> Self:
        if self.worker_task_time_limit <= self.worker_task_soft_time_limit:
            raise ValueError("the task time limit must be greater than the soft time limit")
        return self

    @property
    def database_configured(self) -> bool:
        """Whether a database connection has been configured."""
        return self.database_host is not None

    @property
    def valkey_configured(self) -> bool:
        """Whether a broker connection has been configured."""
        return self.valkey_host is not None

    @property
    def allowed_origin_list(self) -> frozenset[str]:
        """``allowed_origins`` as a set, without trailing slashes."""
        return frozenset(
            origin.strip().rstrip("/")
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        )

    @property
    def session_cookie_name(self) -> str:
        return "__Host-aegis_session" if self.cookie_secure else "aegis_session"

    @property
    def device_cookie_name(self) -> str:
        return "__Host-aegis_device" if self.cookie_secure else "aegis_device"

    @property
    def csrf_cookie_name(self) -> str:
        return "__Host-aegis_csrf" if self.cookie_secure else "aegis_csrf"

    @property
    def docs_enabled(self) -> bool:
        """Whether API documentation is served, after applying the default."""
        if self.api_docs_enabled is not None:
            return self.api_docs_enabled
        return self.environment is not Environment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings, loaded once on first use.

    Secret files are read only when ``AEGIS_SECRETS_DIR`` is set, so a
    missing directory is never searched by accident.
    """
    secrets_dir = os.environ.get(SECRETS_DIR_VARIABLE) or None
    return Settings(_secrets_dir=secrets_dir)  # type: ignore[call-arg]
