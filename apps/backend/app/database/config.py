"""Database connection configuration."""

from http import HTTPStatus

from sqlalchemy import URL

from app.core.config import Settings
from app.core.errors import AppError

DRIVER = "postgresql+psycopg"
APPLICATION_NAME = "aegis-api"
"""Shown in PostgreSQL's ``pg_stat_activity``, to identify AEGIS connections."""


class DatabaseUnavailableError(AppError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "database_unavailable"
    message = "The database is unavailable."


def build_database_url(settings: Settings) -> URL:
    """Build the SQLAlchemy URL from individual settings.

    ``URL.create`` escapes every component, so special characters in the
    password are safe. The password is hidden when the URL is printed or
    logged (``str()``/``repr()``); never render it with ``hide_password=False``.
    """
    if settings.database_host is None:
        raise DatabaseUnavailableError()
    password = settings.database_password
    return URL.create(
        drivername=DRIVER,
        username=settings.database_user,
        password=password.get_secret_value() if password is not None else None,
        host=settings.database_host,
        port=settings.database_port,
        database=settings.database_name,
        query={
            "sslmode": settings.database_sslmode,
            "connect_timeout": str(settings.database_connect_timeout),
            "application_name": APPLICATION_NAME,
        },
    )
