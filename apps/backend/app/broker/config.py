"""Broker connection settings.

Valkey speaks the Redis protocol, so Celery connects through kombu's Redis
transport (``redis://`` or ``rediss://``) and the ``redis`` client library.
kombu has no Valkey-specific transport.
"""

from http import HTTPStatus
from typing import Any
from urllib.parse import quote

from app.core.config import Settings
from app.core.errors import AppError


class BrokerUnavailableError(AppError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "broker_unavailable"
    message = "The message broker is unavailable."


def build_broker_url(settings: Settings) -> str:
    """Build the broker URL for Celery.

    Every component is percent-encoded, so special characters in the
    password are safe. The result contains the password: never log it.
    Celery and kombu mask it in their own output.
    """
    if settings.valkey_host is None:
        raise BrokerUnavailableError()
    scheme = "rediss" if settings.valkey_tls else "redis"
    credentials = ""
    if settings.valkey_username is not None:
        credentials = quote(settings.valkey_username, safe="")
        if settings.valkey_password is not None:
            credentials += ":" + quote(settings.valkey_password.get_secret_value(), safe="")
        credentials += "@"
    host = settings.valkey_host
    if ":" in host:  # IPv6 literal
        host = f"[{host}]"
    url = f"{scheme}://{credentials}{host}:{settings.valkey_port}/{settings.valkey_db}"
    if settings.valkey_tls:
        url += "?ssl_cert_reqs=required"
    return url


def redis_client_options(settings: Settings, client_name: str) -> dict[str, Any]:
    """Keyword arguments for ``redis.Redis``, from the same settings as the broker URL."""
    if settings.valkey_host is None:
        raise BrokerUnavailableError()
    password = settings.valkey_password
    return {
        "host": settings.valkey_host,
        "port": settings.valkey_port,
        "db": settings.valkey_db,
        "username": settings.valkey_username,
        "password": password.get_secret_value() if password is not None else None,
        "ssl": settings.valkey_tls,
        "ssl_cert_reqs": "required",
        "socket_connect_timeout": settings.valkey_connect_timeout,
        "socket_timeout": settings.valkey_socket_timeout,
        "client_name": client_name,
        # Replace idle connections that the server or network has dropped.
        "health_check_interval": 30,
    }
