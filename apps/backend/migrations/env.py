"""Alembic environment.

The connection comes from the application settings (``AEGIS_DATABASE_*``
environment variables), and the target schema from the ORM metadata, so
migrations always use the same configuration and models as the application.

Tests may pass an open connection in ``config.attributes["connection"]`` and
alternative metadata in ``config.attributes["target_metadata"]``.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, create_engine, pool

import app.models  # noqa: F401  (registers every model on Base.metadata)
from app.core.config import get_settings
from app.database.base import Base
from app.database.config import build_database_url

config = context.config

if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# Tests may supply their own metadata to exercise autogeneration.
target_metadata = config.attributes.get("target_metadata", Base.metadata)


def _configure(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )


def run_migrations_offline() -> None:
    """Generate SQL without a database connection (``alembic upgrade --sql``)."""
    context.configure(
        url=build_database_url(get_settings()),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against the database."""
    supplied: Connection | None = config.attributes.get("connection")
    if supplied is not None:
        _configure(supplied)
        with context.begin_transaction():
            context.run_migrations()
        return

    # A dedicated engine without pooling: migrations are short-lived.
    engine = create_engine(
        build_database_url(get_settings()), poolclass=pool.NullPool, hide_parameters=True
    )
    try:
        with engine.connect() as connection:
            _configure(connection)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
