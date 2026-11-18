"""Distributed rate limiting for authentication (DECISIONS.md D-066, D-070).

Counters live in Valkey, so every API process shares them. Counter names are
keyed hashes (HMAC with the server secret): email addresses and client
addresses never appear in Valkey. Every refusal is generic: a throttled
attempt on an unknown account looks exactly like one on a real account.

Sign-in is a two-phase operation, so concurrent requests cannot all pass the
checks before any failure is recorded (D-070):

1. ``begin_login`` **reserves** the attempt. It increments an in-flight
   counter for each applicable scope with one atomic INCRBY, then reads the
   failure counters. The attempt is admitted only if the reservation keeps the
   scope within its limit, counting the other attempts already in flight. A
   refused reservation is released at once.
2. ``finish_login`` releases the reservation. A failure increments the failure
   counters and, past the free failures, sets the progressive delay. A success
   clears the account-and-address counters. Successes never count as failures.

Scopes (defaults; all configurable):

- **Per client address:** at most ``login_ip_max_failures`` (30) failures per
  window (15 minutes), counting attempts in flight.
- **Per account and client address:** the first ``login_pair_free_failures``
  (5) failures are free and attempts may run concurrently. After that, one
  attempt at a time, and each failure blocks the pair for 30, 60, 120, 240,
  480 s, then the window length. Another address is not affected.
- **Per account, any address:** after ``login_account_throttle_failures`` (20)
  failures, one attempt is admitted every ``login_account_delay_seconds``
  (10 s); attempts in between are refused. The delay is set once when an
  attempt is admitted and is never extended by refusals or failures.
- **Trusted device (D-070):** a request carrying a valid, unexpired device
  cookie for that account is exempt from the per-account scope only. The
  per-address and per-account-and-address scopes still apply to it.

There is no permanent lockout. Counters expire with the window, and a
successful sign-in clears its account-and-address counters.

Registration (``registration_ip_max_attempts`` per hour) and password reset
(``password_reset_ip_max_attempts`` per window) are limited per client address.

If Valkey cannot be reached, every action fails closed: it is refused with 503
rather than run without limits.
"""

import logging
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from http import HTTPStatus
from typing import Final, Literal, Protocol

import redis

from app.broker.client import Broker
from app.broker.config import BrokerUnavailableError
from app.core.config import Settings
from app.core.errors import AppError
from app.core.identity import normalize_email_for_lookup
from app.core.security import keyed_hash
from app.core.security_log import security_event

KEY_PREFIX: Final = "ratelimit:"
PAIR_FIRST_DELAY_SECONDS: Final = 30
REGISTRATION_WINDOW_SECONDS: Final = 3600
SENSITIVE_CHANGE_MAX_ATTEMPTS: Final = 5
"""Username and password changes per account in the window below. Every attempt counts."""
SENSITIVE_CHANGE_WINDOW_SECONDS: Final = 900
IN_FLIGHT_TTL_SECONDS: Final = 60
"""Upper bound on how long an in-flight reservation counts if its request dies."""
CONCURRENT_RETRY_MILLISECONDS: Final = 1000
"""Retry hint for an attempt refused only because others are in flight."""

Outcome = Literal["success", "failure", "abandoned"]


class TooManyAttemptsError(AppError):
    status_code = HTTPStatus.TOO_MANY_REQUESTS
    code = "too_many_requests"
    message = "Too many attempts. Wait a moment and try again."

    def __init__(self, retry_after: int) -> None:
        self.retry_after = max(1, retry_after)
        super().__init__(headers={"Retry-After": str(self.retry_after)})


class RateLimiterUnavailableError(AppError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "service_unavailable"
    message = "This action is temporarily unavailable. Try again later."


class RateLimitStore(Protocol):
    """The counter operations the rate limiter needs. Each call is atomic."""

    def counts(self, keys: Sequence[str]) -> list[int]:
        """Current value of each counter (0 if absent)."""

    def remaining_ms(self, keys: Sequence[str]) -> list[int]:
        """Milliseconds until each key expires (0 if absent)."""

    def increment(self, keys: Sequence[str], window_seconds: int, amount: int = 1) -> list[int]:
        """Add ``amount`` (may be negative) to each counter and return the new values.

        A counter without an expiry gets ``window_seconds`` when it is changed.
        """

    def block(self, key: str, milliseconds: int, *, only_if_absent: bool = False) -> bool:
        """Create a marker key that expires after ``milliseconds``; True if it was set.

        With ``only_if_absent``, an existing marker is left unchanged and False is returned.
        """

    def delete(self, keys: Sequence[str]) -> None: ...


class ValkeyRateLimitStore:
    """``RateLimitStore`` on Valkey. Needs only ``ratelimit:*`` keys (ACL, D-066).

    The broker is looked up on every call, so the application's broker can be
    replaced (for example in tests) after the store is created. Multi-key
    updates run in one MULTI/EXEC transaction.
    """

    def __init__(self, broker: Callable[[], Broker]) -> None:
        self._get_broker = broker

    @property
    def _broker(self) -> Broker:
        return self._get_broker()

    def counts(self, keys: Sequence[str]) -> list[int]:
        values = self._broker.client.mget(list(keys))
        return [int(value) if value is not None else 0 for value in values]

    def remaining_ms(self, keys: Sequence[str]) -> list[int]:
        pipe = self._broker.client.pipeline(transaction=False)
        for key in keys:
            pipe.pttl(key)
        return [max(0, int(value)) for value in pipe.execute()]

    def increment(self, keys: Sequence[str], window_seconds: int, amount: int = 1) -> list[int]:
        pipe = self._broker.client.pipeline(transaction=True)
        for key in keys:
            pipe.incrby(key, amount)
            pipe.expire(key, window_seconds, nx=True)
        results = pipe.execute()
        return [int(value) for value in results[0::2]]

    def block(self, key: str, milliseconds: int, *, only_if_absent: bool = False) -> bool:
        return bool(self._broker.client.set(key, "1", px=milliseconds, nx=only_if_absent))

    def delete(self, keys: Sequence[str]) -> None:
        self._broker.client.delete(*keys)


@dataclass(frozen=True)
class _LoginKeys:
    ip_failures: str
    ip_in_flight: str
    pair_failures: str
    pair_in_flight: str
    pair_block: str
    account_failures: str
    account_in_flight: str
    account_block: str


class LoginAttempt:
    """A reserved sign-in attempt. Pass it to ``finish_login`` exactly once."""

    def __init__(self, keys: _LoginKeys, *, trusted_device: bool, client_ip: str) -> None:
        self.keys = keys
        self.trusted_device = trusted_device
        self.client_ip = client_ip
        self.finished = False


class AuthRateLimiter:
    def __init__(self, store: RateLimitStore, settings: Settings, secret: bytes) -> None:
        self._store = store
        self._settings = settings
        self._secret = secret

    # --- key naming -------------------------------------------------------

    def _name(self, kind: str, value: str) -> str:
        return f"{KEY_PREFIX}{kind}:{keyed_hash(self._secret, value)[:40]}"

    def _login_keys(self, email: str, client_ip: str) -> _LoginKeys:
        # The same normalization as registration, so equivalent addresses share counters (D-071).
        normalized = normalize_email_for_lookup(email)
        pair = f"{normalized}\n{client_ip}"
        return _LoginKeys(
            ip_failures=self._name("login:ip", client_ip),
            ip_in_flight=self._name("login:ip-in-flight", client_ip),
            pair_failures=self._name("login:pair", pair),
            pair_in_flight=self._name("login:pair-in-flight", pair),
            pair_block=self._name("login:pair-block", pair),
            account_failures=self._name("login:account", normalized),
            account_in_flight=self._name("login:account-in-flight", normalized),
            account_block=self._name("login:account-block", normalized),
        )

    # --- sign-in ----------------------------------------------------------

    def begin_login(
        self, email: str, client_ip: str, *, trusted_device: bool = False
    ) -> LoginAttempt:
        """Reserve an attempt, or raise ``TooManyAttemptsError`` before any password check.

        Order matters: the reservation is made first, then blocks and failure
        counts are read. A failure that finishes concurrently sets its block
        before it releases its reservation, so an attempt that reserved after
        that release always sees the block.
        """
        keys = self._login_keys(email, client_ip)
        account = not trusted_device
        settings = self._settings
        in_flight_keys = [keys.ip_in_flight, keys.pair_in_flight]
        failure_keys = [keys.ip_failures, keys.pair_failures]
        block_keys = [keys.pair_block]
        if account:
            in_flight_keys.append(keys.account_in_flight)
            failure_keys.append(keys.account_failures)
            block_keys.append(keys.account_block)

        with self._guard("login"):
            in_flight = self._store.increment(in_flight_keys, IN_FLIGHT_TTL_SECONDS)
            try:
                remaining = self._store.remaining_ms(block_keys)
                failures = self._store.counts(failure_keys)
                ip_others = in_flight[0] - 1
                pair_others = in_flight[1] - 1
                ip_failures, pair_failures = failures[0], failures[1]

                if remaining[0] > 0:
                    self._refuse("login_account_ip", client_ip, remaining[0])
                if account and remaining[1] > 0:
                    self._refuse("login_account", client_ip, remaining[1])
                if ip_failures + ip_others >= settings.login_ip_max_failures:
                    self._refuse("login_ip", client_ip, self._ttl(keys.ip_failures))
                if (
                    pair_others > 0
                    and pair_failures + pair_others >= settings.login_pair_free_failures
                ):
                    self._refuse("login_in_progress", client_ip, CONCURRENT_RETRY_MILLISECONDS)

                spacing = False
                if account:
                    account_others = in_flight[2] - 1
                    account_failures = failures[2]
                    if account_others > 0:
                        if (
                            account_failures + account_others
                            >= settings.login_account_throttle_failures
                        ):
                            self._refuse(
                                "login_in_progress", client_ip, CONCURRENT_RETRY_MILLISECONDS
                            )
                    elif account_failures >= settings.login_account_throttle_failures:
                        spacing = True
                if spacing and not self._store.block(
                    keys.account_block,
                    settings.login_account_delay_seconds * 1000,
                    only_if_absent=True,
                ):
                    # Another attempt set the delay after our block check.
                    self._refuse("login_account", client_ip, self._ttl(keys.account_block))
            except BaseException:
                self._store.increment(in_flight_keys, IN_FLIGHT_TTL_SECONDS, amount=-1)
                raise
        return LoginAttempt(keys, trusted_device=trusted_device, client_ip=client_ip)

    def finish_login(self, attempt: LoginAttempt, outcome: Outcome) -> None:
        """Release a reservation and record the outcome.

        ``abandoned`` is used when the attempt did not reach a password decision
        (for example a database error): it is released without counting.
        """
        if attempt.finished:
            raise RuntimeError("a login attempt is finished only once")
        attempt.finished = True
        keys = attempt.keys
        settings = self._settings
        account = not attempt.trusted_device
        with self._guard("login"):
            if outcome == "failure":
                failure_keys = [keys.ip_failures, keys.pair_failures]
                if account:
                    failure_keys.append(keys.account_failures)
                counts = self._store.increment(failure_keys, settings.rate_limit_window_seconds)
                pair_count = counts[1]
                free = settings.login_pair_free_failures
                if pair_count > free:
                    delay = PAIR_FIRST_DELAY_SECONDS * 2 ** (pair_count - free - 1)
                    window = settings.rate_limit_window_seconds
                    self._store.block(keys.pair_block, min(delay, window) * 1000)
            elif outcome == "success":
                self._store.delete([keys.pair_failures, keys.pair_block])

            in_flight_keys = [keys.ip_in_flight, keys.pair_in_flight]
            if account:
                in_flight_keys.append(keys.account_in_flight)
            self._store.increment(in_flight_keys, IN_FLIGHT_TTL_SECONDS, amount=-1)

    # --- other actions ----------------------------------------------------

    def hit_registration(self, client_ip: str) -> None:
        self._hit(
            "registration",
            client_ip,
            self._settings.registration_ip_max_attempts,
            REGISTRATION_WINDOW_SECONDS,
        )

    def hit_sensitive_change(self, user_id: str) -> None:
        """Count one attempt to change the username or password of an account.

        Keyed by account, not address: a signed-in user's current password is
        what is guessed here, so the limit follows the account. The refusal
        names no address, because the account's own requests are the subject.
        """
        key = self._name("account-change", user_id)
        with self._guard("account_change"):
            [count] = self._store.increment([key], SENSITIVE_CHANGE_WINDOW_SECONDS)
            if count <= SENSITIVE_CHANGE_MAX_ATTEMPTS:
                return
            ttl = self._ttl(key)
        security_event(
            "auth.rate_limited",
            "Attempt refused by rate limiting",
            level=logging.WARNING,
            scope="account_change",
            user_id=user_id,
        )
        raise TooManyAttemptsError(retry_after=math.ceil(ttl / 1000))

    def hit_password_reset(self, client_ip: str) -> None:
        self._hit(
            "password_reset",
            client_ip,
            self._settings.password_reset_ip_max_attempts,
            self._settings.rate_limit_window_seconds,
        )

    def _hit(self, action: str, client_ip: str, limit: int, window: int) -> None:
        key = self._name(action, client_ip)
        with self._guard(action):
            [count] = self._store.increment([key], window)
            if count <= limit:
                return
            ttl = self._ttl(key)
        self._refuse(action, client_ip, ttl)

    # --- helpers ----------------------------------------------------------

    def _ttl(self, key: str) -> int:
        """Milliseconds until ``key`` expires, at least one second."""
        [remaining] = self._store.remaining_ms([key])
        return max(remaining, CONCURRENT_RETRY_MILLISECONDS)

    def _refuse(self, scope: str, client_ip: str, remaining_ms: int) -> None:
        security_event(
            "auth.rate_limited",
            "Attempt refused by rate limiting",
            level=logging.WARNING,
            scope=scope,
            client_ip=client_ip,
        )
        raise TooManyAttemptsError(retry_after=math.ceil(remaining_ms / 1000))

    def _guard(self, action: str) -> "_StoreGuard":
        return _StoreGuard(action)


class _StoreGuard:
    """Turn any Valkey failure into a fail-closed 503."""

    def __init__(self, action: str) -> None:
        self._action = action

    def __enter__(self) -> None:
        return None

    def __exit__(self, exc_type: object, exc: BaseException | None, tb: object) -> Literal[False]:
        if isinstance(exc, (redis.RedisError, BrokerUnavailableError, OSError)):
            security_event(
                "auth.rate_limiter_unavailable",
                "Rate limiter unavailable; action refused",
                level=logging.ERROR,
                action=self._action,
                error_type=type(exc).__name__,
            )
            raise RateLimiterUnavailableError() from exc
        return False
