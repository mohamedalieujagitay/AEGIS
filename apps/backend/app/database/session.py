"""Database lifecycle and session management.

One ``Database`` object is created per application. It creates the engine
lazily, on first use, so importing or starting the application never opens
a connection, and it disposes of the connection pool on shutdown.

Each API request that needs the database gets one session through the
``get_db_session`` dependency. The session's transaction is committed when
the request handler returns and rolled back if it raises.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import Request
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.database.config import DatabaseUnavailableError
from app.database.engine import create_database_engine

logger = logging.getLogger("app.database")


class Database:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None

    @property
    def configured(self) -> bool:
        return self._settings.database_configured

    @property
    def engine(self) -> Engine:
        """The engine, created on first access."""
        if self._engine is None:
            if not self.configured:
                raise DatabaseUnavailableError()
            self._engine = create_database_engine(self._settings)
            # Host, port and database name only: never the user or password.
            logger.info(
                "Database engine created",
                extra={
                    "event": "database.engine_created",
                    "db_host": self._settings.database_host,
                    "db_port": self._settings.database_port,
                    "db_name": self._settings.database_name,
                    "db_sslmode": self._settings.database_sslmode,
                },
            )
        return self._engine

    @property
    def session_factory(self) -> sessionmaker[Session]:
        if self._session_factory is None:
            # expire_on_commit=False lets handlers return loaded objects
            # after the transaction has been committed.
            self._session_factory = sessionmaker(
                bind=self.engine, autoflush=False, expire_on_commit=False
            )
        return self._session_factory

    @contextmanager
    def session(self) -> Iterator[Session]:
        """A session in a transaction: committed on success, rolled back on error."""
        with self.session_factory.begin() as session:
            yield session

    def ping(self) -> None:
        """Run a trivial query. Raises if the database cannot be reached."""
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def dispose(self) -> None:
        """Close all pooled connections. Safe to call when no engine exists."""
        if self._engine is not None:
            self._engine.dispose()
            logger.info("Database connections closed", extra={"event": "database.disposed"})
        self._engine = None
        self._session_factory = None


def get_database(request: Request) -> Database:
    """The application's ``Database``."""
    database: Database = request.app.state.database
    return database


def get_db_session(request: Request) -> Iterator[Session]:
    """FastAPI dependency: one transactional session per request."""
    with get_database(request).session() as session:
        yield session
