"""Broker client lifecycle.

One ``Broker`` object is created per application. Like ``Database``, it
creates its client lazily, so importing or starting the application never
opens a connection, and closes its connections on shutdown. The client keeps
a small connection pool, so repeated readiness checks reuse connections.
"""

import logging
from typing import Any

import redis

from app.broker.config import BrokerUnavailableError, redis_client_options
from app.core.config import Settings

logger = logging.getLogger("app.broker")

MAX_CONNECTIONS = 4
"""Connections kept by the API's broker client (readiness checks only)."""


class Broker:
    def __init__(self, settings: Settings, client_name: str = "aegis-api") -> None:
        self._settings = settings
        self._client_name = client_name
        self._client: redis.Redis | None = None

    @property
    def configured(self) -> bool:
        return self._settings.valkey_configured

    @property
    def client(self) -> redis.Redis:
        """The client, created on first access."""
        if self._client is None:
            if not self.configured:
                raise BrokerUnavailableError()
            options = redis_client_options(self._settings, self._client_name)
            use_tls = bool(options.pop("ssl"))
            if not use_tls:
                options = _without_tls(options)
            pool = redis.ConnectionPool(
                max_connections=MAX_CONNECTIONS,
                connection_class=redis.SSLConnection if use_tls else redis.Connection,
                **options,
            )
            self._client = redis.Redis(connection_pool=pool)
            # Host and port only: never the username or password.
            logger.info(
                "Broker client created",
                extra={
                    "event": "broker.client_created",
                    "broker_host": self._settings.valkey_host,
                    "broker_port": self._settings.valkey_port,
                    "broker_tls": self._settings.valkey_tls,
                },
            )
        return self._client

    def ping(self) -> None:
        """Send PING. Raises if the broker cannot be reached or refuses the user."""
        if not self.client.ping():
            raise BrokerUnavailableError()

    def dispose(self) -> None:
        """Close all pooled connections. Safe to call when no client exists."""
        if self._client is not None:
            self._client.connection_pool.disconnect()
            logger.info("Broker connections closed", extra={"event": "broker.disposed"})
        self._client = None


def _without_tls(options: dict[str, Any]) -> dict[str, Any]:
    """Drop TLS-only options, which plain connections do not accept."""
    return {key: value for key, value in options.items() if not key.startswith("ssl_")}
