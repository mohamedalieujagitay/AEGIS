"""Engine creation and connection pooling."""

from sqlalchemy import Engine, create_engine

from app.core.config import Settings
from app.database.config import build_database_url


def create_database_engine(settings: Settings) -> Engine:
    """Create the engine. No connection is opened until the engine is used.

    - ``pool_pre_ping`` checks connections before use, so connections broken
      by a database restart are replaced instead of failing requests.
    - ``hide_parameters`` keeps bound parameter values (which can include
      secrets) out of exception messages and logs.
    - SQL statement logging (``echo``) stays off.
    """
    return create_engine(
        build_database_url(settings),
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout,
        pool_recycle=settings.database_pool_recycle,
        pool_pre_ping=True,
        hide_parameters=True,
        echo=False,
    )
