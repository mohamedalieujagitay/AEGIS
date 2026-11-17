"""Authentication rate limiting (DECISIONS.md D-066, D-070, D-071), including abuse scenarios.

These tests use an in-memory store with Valkey's semantics. The same
behaviour is checked against a real Valkey server in ``test_valkey_rate_limit.py``.
"""

import functools
import itertools
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

import pytest
import redis
from helpers import FakeClock, MemoryRateLimitStore

from app.broker.config import BrokerUnavailableError
from app.core.config import Settings
from app.services.rate_limit import (
    AuthRateLimiter,
    LoginAttempt,
    RateLimiterUnavailableError,
    TooManyAttemptsError,
)

SECRET = b"k" * 32
VICTIM = "victim@example.com"
ATTACKER_IP = "203.0.113.66"
VICTIM_IP = "198.51.100.7"


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def store(clock: FakeClock) -> MemoryRateLimitStore:
    return MemoryRateLimitStore(clock)


@pytest.fixture
def limiter(store: MemoryRateLimitStore) -> AuthRateLimiter:
    return AuthRateLimiter(store, Settings(), SECRET)


def sign_in(
    limiter: AuthRateLimiter,
    email: str,
    ip: str,
    *,
    succeeds: bool,
    trusted: bool = False,
) -> bool:
    """One complete attempt. Returns False if it was refused before the password check."""
    try:
        attempt = limiter.begin_login(email, ip, trusted_device=trusted)
    except TooManyAttemptsError:
        return False
    limiter.finish_login(attempt, "success" if succeeds else "failure")
    return True


def fail(limiter: AuthRateLimiter, email: str, ip: str, times: int) -> None:
    """``times`` failed attempts with no waiting. At most six for one account and address
    (the sixth starts the first delay); use distinct accounts for more."""
    assert times <= 6
    for _ in range(times):
        assert sign_in(limiter, email, ip, succeeds=False)


def fail_many_accounts(limiter: AuthRateLimiter, ip: str, count: int) -> None:
    """Failures from one address against different accounts (the per-address scope)."""
    for index in range(count):
        assert sign_in(limiter, f"user{index}@example.com", ip, succeeds=False)


def refused_for(limiter: AuthRateLimiter, email: str, ip: str) -> int | None:
    """Seconds an attempt is refused for, or None if it is admitted (then released)."""
    try:
        attempt = limiter.begin_login(email, ip)
    except TooManyAttemptsError as error:
        return error.retry_after
    limiter.finish_login(attempt, "abandoned")
    return None


# --- progressive delays per account and address -------------------------------


def test_first_failures_are_free(limiter: AuthRateLimiter) -> None:
    fail(limiter, VICTIM, ATTACKER_IP, 5)
    assert refused_for(limiter, VICTIM, ATTACKER_IP) is None


def test_each_failure_past_the_free_ones_doubles_the_delay(
    limiter: AuthRateLimiter, clock: FakeClock
) -> None:
    fail(limiter, VICTIM, ATTACKER_IP, 5)
    delays = []
    for _ in range(5):
        assert sign_in(limiter, VICTIM, ATTACKER_IP, succeeds=False)
        delay = refused_for(limiter, VICTIM, ATTACKER_IP)
        assert delay is not None
        delays.append(delay)
        clock.advance(seconds=delay)
    assert delays == [30, 60, 120, 240, 480]


def test_delays_never_exceed_the_window(store: MemoryRateLimitStore, clock: FakeClock) -> None:
    limiter = AuthRateLimiter(store, Settings(rate_limit_window_seconds=100), SECRET)
    fail(limiter, VICTIM, ATTACKER_IP, 5)
    delays = []
    for _ in range(3):
        assert sign_in(limiter, VICTIM, ATTACKER_IP, succeeds=False)
        delay = refused_for(limiter, VICTIM, ATTACKER_IP)
        assert delay is not None
        delays.append(delay)
        clock.advance(seconds=delay)
    assert delays == [30, 60, 100]  # 120 would be the next step; capped at the window


def test_a_successful_sign_in_clears_the_pair(limiter: AuthRateLimiter) -> None:
    fail(limiter, VICTIM, VICTIM_IP, 5)
    assert sign_in(limiter, VICTIM, VICTIM_IP, succeeds=True)
    fail(limiter, VICTIM, VICTIM_IP, 5)
    assert refused_for(limiter, VICTIM, VICTIM_IP) is None


def test_limits_are_configurable(store: MemoryRateLimitStore) -> None:
    limiter = AuthRateLimiter(store, Settings(login_pair_free_failures=1), SECRET)
    fail(limiter, VICTIM, VICTIM_IP, 2)
    assert refused_for(limiter, VICTIM, VICTIM_IP) == 30


def test_another_address_is_not_affected_by_one_address_failing(
    limiter: AuthRateLimiter,
) -> None:
    fail(limiter, VICTIM, ATTACKER_IP, 6)
    assert refused_for(limiter, VICTIM, ATTACKER_IP) is not None
    assert refused_for(limiter, VICTIM, VICTIM_IP) is None


# --- per address -----------------------------------------------------------------


def test_one_address_is_limited_across_accounts(limiter: AuthRateLimiter) -> None:
    """Spraying many accounts from one address is stopped by the per-address limit."""
    fail_many_accounts(limiter, ATTACKER_IP, 30)
    assert refused_for(limiter, "another@example.com", ATTACKER_IP) is not None
    assert refused_for(limiter, "another@example.com", VICTIM_IP) is None


def test_per_address_refusals_carry_a_retry_hint(limiter: AuthRateLimiter) -> None:
    fail_many_accounts(limiter, ATTACKER_IP, 30)
    delay = refused_for(limiter, "another@example.com", ATTACKER_IP)
    assert delay is not None
    assert 0 < delay <= Settings().rate_limit_window_seconds


# --- the account-wide scope and the distributed attack (H-1) ----------------------


def test_twenty_failures_from_many_addresses_slow_the_account(
    limiter: AuthRateLimiter, clock: FakeClock
) -> None:
    for index in range(20):
        fail(limiter, VICTIM, f"203.0.113.{index}", 1)
    # The first attempt after the threshold is admitted and starts the delay...
    assert refused_for(limiter, VICTIM, VICTIM_IP) is None
    # ...then attempts are refused until it has passed.
    assert refused_for(limiter, VICTIM, VICTIM_IP) == Settings().login_account_delay_seconds
    clock.advance(seconds=Settings().login_account_delay_seconds)
    assert refused_for(limiter, VICTIM, VICTIM_IP) is None


def test_refusals_do_not_extend_the_account_delay(
    limiter: AuthRateLimiter, clock: FakeClock
) -> None:
    """The delay is set once per admitted attempt, so refused attempts cannot prolong it."""
    for index in range(20):
        fail(limiter, VICTIM, f"203.0.113.{index}", 1)
    admitted_at: list[float] = []
    for second in range(120):  # a new address every second, for two minutes
        clock.advance(seconds=1)
        if sign_in(limiter, VICTIM, f"198.18.0.{second % 250}", succeeds=False):
            admitted_at.append(clock().timestamp())
    gaps = {round(later - earlier) for earlier, later in itertools.pairwise(admitted_at)}
    assert gaps == {Settings().login_account_delay_seconds}


def test_rotating_addresses_cannot_lock_out_the_account_owner(
    store: MemoryRateLimitStore, clock: FakeClock
) -> None:
    """Regression for the attack found in the engineering review (H-1).

    Before the fix, an attacker rotating through 20 addresses kept the owner
    blocked for 3,541 of 3,600 seconds: every failure re-set the account-wide
    delay, and the owner, signing in from an ordinary address, was refused.

    Here the owner signs in from a browser with a device token (``trusted``).
    For an hour the attacker tries once a second, each time from a different
    address. The owner must be admitted every second, and the attacker must
    stay at the account-wide rate of one attempt per delay.
    """
    limiter = AuthRateLimiter(store, Settings(), SECRET)
    attacker_ips = [f"203.0.113.{index}" for index in range(20)]
    for ip in attacker_ips:
        fail(limiter, VICTIM, ip, 1)

    owner_admitted = 0
    attacker_admitted = 0
    for second in range(3600):
        clock.advance(seconds=1)
        if sign_in(limiter, VICTIM, attacker_ips[second % len(attacker_ips)], succeeds=False):
            attacker_admitted += 1
        if sign_in(limiter, VICTIM, VICTIM_IP, succeeds=True, trusted=True):
            owner_admitted += 1

    assert owner_admitted == 3600
    # Bound: one attempt per delay, plus a burst of up to 20 each time the 15-minute
    # account counter resets (D-070, accepted limitation SR-010).
    settings = Settings()
    window = settings.rate_limit_window_seconds
    bound = (
        3600 // settings.login_account_delay_seconds
        + settings.login_account_throttle_failures * (3600 // window + 1)
    )
    assert attacker_admitted <= bound


def test_without_a_device_token_a_new_browser_still_waits_during_an_attack(
    store: MemoryRateLimitStore, clock: FakeClock
) -> None:
    """Documents the residual risk (SR-009). The device token is the only exemption.

    An owner signing in from a browser without a device token competes with the
    attacker for the single attempt the account-wide delay admits, so some
    attempts are refused while the attack lasts.
    """
    limiter = AuthRateLimiter(store, Settings(), SECRET)
    attacker_ips = [f"203.0.113.{index}" for index in range(20)]
    for ip in attacker_ips:
        fail(limiter, VICTIM, ip, 1)
    owner_refused = 0
    for second in range(120):
        clock.advance(seconds=1)
        sign_in(limiter, VICTIM, attacker_ips[second % 20], succeeds=False)
        if not sign_in(limiter, VICTIM, VICTIM_IP, succeeds=True):
            owner_refused += 1
    assert owner_refused > 0


def test_a_device_token_does_not_exempt_the_address_limits(limiter: AuthRateLimiter) -> None:
    """A trusted device still faces the per-address limit (30 failures per window)."""
    for index in range(30):
        assert sign_in(
            limiter, f"user{index}@example.com", ATTACKER_IP, succeeds=False, trusted=True
        )
    assert not sign_in(limiter, VICTIM, ATTACKER_IP, succeeds=False, trusted=True)


def test_a_device_token_does_not_exempt_the_pair_delay(limiter: AuthRateLimiter) -> None:
    fail(limiter, VICTIM, ATTACKER_IP, 6)  # the sixth failure starts the 30 s delay
    assert not sign_in(limiter, VICTIM, ATTACKER_IP, succeeds=True, trusted=True)


# --- concurrency: reservations are atomic (M-1) -------------------------------------


def parallel_begin(
    calls: list[Callable[[], LoginAttempt]],
) -> tuple[list[LoginAttempt], int]:
    """Start every attempt at once; returns the admitted attempts and the refused count."""
    with ThreadPoolExecutor(max_workers=len(calls)) as pool:
        futures = [pool.submit(call) for call in calls]
        admitted: list[LoginAttempt] = []
        refused = 0
        for future in futures:
            try:
                admitted.append(future.result())
            except TooManyAttemptsError:
                refused += 1
    return admitted, refused


def test_parallel_attempts_on_one_pair_respect_the_free_failures(
    limiter: AuthRateLimiter,
) -> None:
    """Fifty simultaneous attempts: only the five free ones run at once."""
    calls: list[Callable[[], LoginAttempt]] = [
        (lambda: limiter.begin_login(VICTIM, VICTIM_IP)) for _ in range(50)
    ]
    admitted, refused = parallel_begin(calls)
    assert len(admitted) == Settings().login_pair_free_failures
    assert refused == 50 - len(admitted)
    for attempt in admitted:
        limiter.finish_login(attempt, "abandoned")


def test_after_the_free_failures_only_one_attempt_runs_at_a_time(
    limiter: AuthRateLimiter,
) -> None:
    fail(limiter, VICTIM, VICTIM_IP, 5)
    calls: list[Callable[[], LoginAttempt]] = [
        (lambda: limiter.begin_login(VICTIM, VICTIM_IP)) for _ in range(50)
    ]
    admitted, refused = parallel_begin(calls)
    assert len(admitted) == 1
    assert refused == 49
    limiter.finish_login(admitted[0], "abandoned")


def test_parallel_attempts_on_one_account_from_many_addresses_admit_one(
    limiter: AuthRateLimiter,
) -> None:
    for index in range(20):
        fail(limiter, VICTIM, f"203.0.113.{index}", 1)
    calls: list[Callable[[], LoginAttempt]] = [
        functools.partial(limiter.begin_login, VICTIM, f"198.18.0.{index}") for index in range(50)
    ]
    admitted, refused = parallel_begin(calls)
    assert len(admitted) == 1
    assert refused == 49
    limiter.finish_login(admitted[0], "abandoned")


def test_a_refused_reservation_leaves_no_in_flight_count(
    store: MemoryRateLimitStore, limiter: AuthRateLimiter
) -> None:
    fail(limiter, VICTIM, VICTIM_IP, 5)
    held = limiter.begin_login(VICTIM, VICTIM_IP)
    with pytest.raises(TooManyAttemptsError):
        limiter.begin_login(VICTIM, VICTIM_IP)
    limiter.finish_login(held, "abandoned")
    # Nothing is left reserved: the next attempt is admitted at once.
    assert refused_for(limiter, VICTIM, VICTIM_IP) is None
    assert store.counts(store.keys()) != []  # the store still holds the window counters


def test_an_attempt_can_be_finished_only_once(limiter: AuthRateLimiter) -> None:
    attempt = limiter.begin_login(VICTIM, VICTIM_IP)
    limiter.finish_login(attempt, "abandoned")
    with pytest.raises(RuntimeError):
        limiter.finish_login(attempt, "failure")


def test_successes_are_never_counted_as_failures(limiter: AuthRateLimiter) -> None:
    for _ in range(50):
        assert sign_in(limiter, VICTIM, VICTIM_IP, succeeds=True)


# --- equivalent addresses share counters (D-071) -----------------------------------


def test_equivalent_spellings_of_an_address_share_rate_limit_counters(
    limiter: AuthRateLimiter,
) -> None:
    fail(limiter, "User@Bücher.example", VICTIM_IP, 5)
    assert refused_for(limiter, "user@xn--bcher-kva.example", VICTIM_IP) is None
    fail(limiter, "USER@BÜCHER.EXAMPLE", VICTIM_IP, 1)  # the sixth failure, shared counter
    assert refused_for(limiter, "user@bücher.example", VICTIM_IP) == 30


def test_malformed_emails_are_limited_without_crashing(limiter: AuthRateLimiter) -> None:
    for email in (
        "",
        "no-at-sign",
        "a@b@c",
        "@",
        "x" * 500,
        "user@\u0000.example",
        "🙂@🙂.example",
    ):
        assert sign_in(limiter, email, VICTIM_IP, succeeds=False)


# --- other scopes --------------------------------------------------------------------


def test_registration_and_reset_are_limited_per_address(limiter: AuthRateLimiter) -> None:
    for _ in range(5):
        limiter.hit_registration(ATTACKER_IP)
    with pytest.raises(TooManyAttemptsError) as registration:
        limiter.hit_registration(ATTACKER_IP)
    assert 0 < registration.value.retry_after <= 3600
    limiter.hit_registration(VICTIM_IP)

    for _ in range(10):
        limiter.hit_password_reset(ATTACKER_IP)
    with pytest.raises(TooManyAttemptsError):
        limiter.hit_password_reset(ATTACKER_IP)
    limiter.hit_password_reset(VICTIM_IP)


def test_counter_names_reveal_neither_email_nor_address(
    limiter: AuthRateLimiter, store: MemoryRateLimitStore
) -> None:
    fail(limiter, VICTIM, VICTIM_IP, 6)
    limiter.hit_registration(VICTIM_IP)
    keys = store.keys()
    assert keys
    assert all(key.startswith("ratelimit:") for key in keys)
    joined = " ".join(keys)
    assert "victim" not in joined
    assert VICTIM_IP not in joined


def test_throttling_is_logged_without_the_email(
    limiter: AuthRateLimiter, caplog: pytest.LogCaptureFixture
) -> None:
    fail(limiter, VICTIM, VICTIM_IP, 6)
    with caplog.at_level(logging.WARNING, logger="app.security"):
        assert refused_for(limiter, VICTIM, VICTIM_IP) is not None
    [record] = [r for r in caplog.records if getattr(r, "event", None) == "auth.rate_limited"]
    assert record.__dict__["scope"] == "login_account_ip"
    assert VICTIM not in caplog.text


@pytest.mark.parametrize(
    "failure",
    [redis.ConnectionError("down"), redis.TimeoutError("slow"), BrokerUnavailableError()],
)
def test_store_failures_fail_closed(
    limiter: AuthRateLimiter,
    store: MemoryRateLimitStore,
    caplog: pytest.LogCaptureFixture,
    failure: Exception,
) -> None:
    store.fail_with = failure
    with caplog.at_level(logging.ERROR, logger="app.security"):
        actions: list[Callable[[], object]] = [
            lambda: limiter.begin_login(VICTIM, VICTIM_IP),
            lambda: limiter.hit_registration(VICTIM_IP),
            lambda: limiter.hit_password_reset(VICTIM_IP),
        ]
        for action in actions:
            with pytest.raises(RateLimiterUnavailableError):
                action()
    assert any(getattr(r, "event", None) == "auth.rate_limiter_unavailable" for r in caplog.records)


def test_a_failed_finish_is_reported_not_swallowed(
    limiter: AuthRateLimiter, store: MemoryRateLimitStore
) -> None:
    attempt = limiter.begin_login(VICTIM, VICTIM_IP)
    store.fail_with = redis.ConnectionError("down")
    with pytest.raises(RateLimiterUnavailableError):
        limiter.finish_login(attempt, "failure")
