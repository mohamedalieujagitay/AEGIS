"""Shared test helpers for authentication."""

import threading
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.csrf import CSRF_HEADER, csrf_binding, issue_csrf_token

TEST_SECRET_KEY = "test-secret-key-not-for-production-0123456789abcdef"
UNSAFE = {"POST", "PUT", "PATCH", "DELETE"}
COOKIE_DOMAIN = "testserver.local"


class FakeClock:
    """A controllable replacement for ``app.core.clock.utcnow``."""

    def __init__(self, start: datetime | None = None) -> None:
        self.now = start or datetime(2026, 11, 17, 9, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **delta: float) -> None:
        self.now += timedelta(**delta)


class MemoryRateLimitStore:
    """In-memory ``RateLimitStore`` with Valkey's semantics: expiry, atomic updates.

    Every operation holds one lock, as Valkey's single-threaded execution does,
    so concurrent threads see the same results as concurrent Valkey clients.
    """

    def __init__(self, clock: FakeClock) -> None:
        self._clock = clock
        self._data: dict[str, tuple[int, float | None]] = {}
        self._lock = threading.Lock()
        self.fail_with: Exception | None = None

    def _now_ms(self) -> float:
        return self._clock().timestamp() * 1000

    def _live(self, key: str) -> tuple[int, float | None] | None:
        entry = self._data.get(key)
        if entry is not None and entry[1] is not None and entry[1] <= self._now_ms():
            del self._data[key]
            return None
        return entry

    def _check(self) -> None:
        if self.fail_with is not None:
            raise self.fail_with

    def keys(self) -> list[str]:
        with self._lock:
            return [key for key in list(self._data) if self._live(key) is not None]

    def counts(self, keys: Sequence[str]) -> list[int]:
        with self._lock:
            self._check()
            return [entry[0] if (entry := self._live(key)) else 0 for key in keys]

    def remaining_ms(self, keys: Sequence[str]) -> list[int]:
        with self._lock:
            self._check()
            result = []
            for key in keys:
                entry = self._live(key)
                result.append(int(entry[1] - self._now_ms()) if entry and entry[1] else 0)
            return result

    def increment(self, keys: Sequence[str], window_seconds: int, amount: int = 1) -> list[int]:
        with self._lock:
            self._check()
            values = []
            for key in keys:
                entry = self._live(key)
                expires = entry[1] if entry and entry[1] is not None else None
                if expires is None:
                    expires = self._now_ms() + window_seconds * 1000
                value = (entry[0] if entry else 0) + amount
                self._data[key] = (value, expires)
                values.append(value)
            return values

    def block(self, key: str, milliseconds: int, *, only_if_absent: bool = False) -> bool:
        with self._lock:
            self._check()
            if only_if_absent and self._live(key) is not None:
                return False
            self._data[key] = (1, self._now_ms() + milliseconds)
            return True

    def delete(self, keys: Sequence[str]) -> None:
        with self._lock:
            self._check()
            for key in keys:
                self._data.pop(key, None)


class AegisTestClient(TestClient):
    """Test client that behaves like the AEGIS frontend.

    It uses HTTPS (so ``Secure`` cookies are sent back) and, unless
    ``auto_csrf`` is False or the request sets ``X-CSRF-Token`` itself, adds a
    CSRF token bound to its current session, exactly as the browser would
    after calling ``GET /api/v1/auth/csrf``.
    """

    def __init__(self, app: FastAPI, *, auto_csrf: bool = True, **kwargs: Any) -> None:
        kwargs.setdefault("base_url", "https://testserver")
        super().__init__(app, **kwargs)
        self.auto_csrf = auto_csrf
        self._app = app

    def _settings(self) -> Any:
        return self._app.state.auth.settings

    def csrf_token(self) -> str:
        """A valid token for the current session, also stored in the CSRF cookie."""
        from app.core import clock

        token = issue_csrf_token(
            self._app.state.auth.secret,
            csrf_binding(self.session_cookie()),
            int(clock.utcnow().timestamp()),
        )
        self.set_cookie(self._settings().csrf_cookie_name, token)
        return token

    def set_cookie(self, name: str, value: str) -> None:
        """Set a cookie as if the server had (replacing the server's copy, if any).

        The standard cookie jar files host-only cookies for ``testserver``
        under ``testserver.local``.
        """
        self.cookies.set(name, value, domain=COOKIE_DOMAIN, path="/")

    def session_cookie(self) -> str | None:
        return self.cookies.get(self._settings().session_cookie_name, domain=COOKIE_DOMAIN)

    def request(self, method: str, url: Any, *args: Any, **kwargs: Any) -> Any:
        if self.auto_csrf and method.upper() in UNSAFE:
            headers = dict(kwargs.pop("headers", None) or {})
            if CSRF_HEADER not in headers:
                headers[CSRF_HEADER] = self.csrf_token()
            kwargs["headers"] = headers
        return super().request(method, url, *args, **kwargs)
