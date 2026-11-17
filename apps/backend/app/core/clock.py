"""The application's clock.

Authentication code reads the time only through ``utcnow`` so that tests can
move time forward (session expiry, token lifetimes) without sleeping.
"""

from datetime import UTC, datetime


def utcnow() -> datetime:
    """The current time in UTC, timezone-aware."""
    return datetime.now(UTC)
