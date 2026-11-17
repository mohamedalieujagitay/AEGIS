"""Rate limiting against a real Valkey server (DECISIONS.md D-066, D-070).

These tests run only when a Valkey server is provided for the test run:

    AEGIS_TEST_VALKEY_HOST=127.0.0.1 AEGIS_TEST_VALKEY_PORT=16390 \
        pytest tests/test_valkey_rate_limit.py

Set AEGIS_TEST_REQUIRE_VALKEY=1 to fail, instead of skip, when it is missing.
The server must be disposable: the tests flush database 9 of it. Read at import
time because the settings fixture clears AEGIS_* variables for each test.
"""

import os
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.broker.client import Broker
from app.core.config import Environment, Settings
from app.services.rate_limit import (
    AuthRateLimiter,
    LoginAttempt,
    RateLimiterUnavailableError,
    TooManyAttemptsError,
    ValkeyRateLimitStore,
)

HOST = os.environ.get("AEGIS_TEST_VALKEY_HOST")
PORT = int(os.environ.get("AEGIS_TEST_VALKEY_PORT", "6379"))
REQUIRED = os.environ.get("AEGIS_TEST_REQUIRE_VALKEY") == "1"
SECRET = b"v" * 32
TEST_DB = 9

pytestmark = pytest.mark.skipif(
    HOST is None and not REQUIRED,
    reason="no Valkey server for the test run (set AEGIS_TEST_VALKEY_HOST)",
)


@pytest.fixture
def settings() -> Settings:
    if HOST is None:
        pytest.fail("AEGIS_TEST_REQUIRE_VALKEY=1 but AEGIS_TEST_VALKEY_HOST is not set")
    return Settings(
        environment=Environment.TEST,
        valkey_host=HOST,
        valkey_port=PORT,
        valkey_db=TEST_DB,
    )


@pytest.fixture
def broker(settings: Settings) -> Iterator[Broker]:
    broker = Broker(settings)
    broker.client.flushdb()
    yield broker
    broker.client.flushdb()
    broker.dispose()


@pytest.fixture
def limiter(broker: Broker, settings: Settings) -> AuthRateLimiter:
    return AuthRateLimiter(ValkeyRateLimitStore(lambda: broker), settings, SECRET)


VICTIM = "victim@example.com"
VICTIM_IP = "198.51.100.7"


def test_counters_expire_on_the_server(broker: Broker, settings: Settings) -> None:
    store = ValkeyRateLimitStore(lambda: broker)
    store.increment(["ratelimit:probe"], window_seconds=60)
    [remaining] = store.remaining_ms(["ratelimit:probe"])
    assert 0 < remaining <= 60_000
    store.block("ratelimit:blocked", 1200)
    assert store.remaining_ms(["ratelimit:blocked"])[0] > 0
    time.sleep(1.5)
    assert store.remaining_ms(["ratelimit:blocked"]) == [0]


def test_only_the_first_block_is_set_when_only_if_absent(broker: Broker) -> None:
    store = ValkeyRateLimitStore(lambda: broker)
    assert store.block("ratelimit:once", 10_000, only_if_absent=True) is True
    assert store.block("ratelimit:once", 10_000, only_if_absent=True) is False


def test_no_reservation_is_left_without_an_expiry(limiter: AuthRateLimiter, broker: Broker) -> None:
    """Every in-flight counter has a time limit, so a crashed request cannot leak one forever."""
    for _ in range(3):
        attempt = limiter.begin_login(VICTIM, VICTIM_IP)
        limiter.finish_login(attempt, "failure")
    for _ in range(2):
        attempt = limiter.begin_login(VICTIM, VICTIM_IP)
        limiter.finish_login(attempt, "abandoned")
    client = broker.client
    keys = list(client.scan_iter(match="ratelimit:*"))
    assert keys
    assert all(client.pttl(key) != -1 for key in keys)


def test_fifty_parallel_attempts_on_one_pair_admit_the_free_five(
    limiter: AuthRateLimiter, settings: Settings
) -> None:
    """The atomicity claim (M-1) checked against the real server."""
    with ThreadPoolExecutor(max_workers=50) as pool:
        results: list[LoginAttempt | None] = list(
            pool.map(lambda _: _try_begin(limiter), range(50))
        )
    admitted = [attempt for attempt in results if attempt is not None]
    assert len(admitted) == settings.login_pair_free_failures
    for attempt in admitted:
        limiter.finish_login(attempt, "abandoned")


def test_parallel_attempts_on_one_account_from_many_addresses_admit_one(
    limiter: AuthRateLimiter,
) -> None:
    for index in range(20):
        attempt = limiter.begin_login(VICTIM, f"203.0.113.{index}")
        limiter.finish_login(attempt, "failure")

    def begin(index: int) -> object:
        return _try_begin(limiter, ip=f"198.18.0.{index}")

    with ThreadPoolExecutor(max_workers=50) as pool:
        results = list(pool.map(begin, range(50)))
    admitted = [attempt for attempt in results if attempt is not None]
    assert len(admitted) == 1
    limiter.finish_login(admitted[0], "abandoned")  # type: ignore[arg-type]


def test_a_refusal_for_the_account_delay_is_not_extended(
    limiter: AuthRateLimiter, broker: Broker, settings: Settings
) -> None:
    for index in range(20):
        attempt = limiter.begin_login(VICTIM, f"203.0.113.{index}")
        limiter.finish_login(attempt, "failure")
    first = limiter.begin_login(VICTIM, "198.18.0.1")  # admitted, starts the delay
    limiter.finish_login(first, "abandoned")
    client = broker.client
    account_block = list(client.scan_iter(match="ratelimit:login:account-block:*"))
    assert len(account_block) == 1
    before = client.pttl(account_block[0])
    for index in range(2, 6):
        with pytest.raises(TooManyAttemptsError):
            limiter.begin_login(VICTIM, f"198.18.0.{index}")
    assert client.pttl(account_block[0]) <= before


def test_an_unreachable_valkey_fails_closed(settings: Settings) -> None:
    dead = Settings(
        environment=Environment.TEST, valkey_host="127.0.0.1", valkey_port=1, valkey_db=TEST_DB
    )
    broker = Broker(dead)
    limiter = AuthRateLimiter(ValkeyRateLimitStore(lambda: broker), dead, SECRET)
    with pytest.raises(RateLimiterUnavailableError):
        limiter.begin_login(VICTIM, VICTIM_IP)
    with pytest.raises(RateLimiterUnavailableError):
        limiter.hit_registration(VICTIM_IP)
    broker.dispose()


def _try_begin(limiter: AuthRateLimiter, ip: str = VICTIM_IP) -> LoginAttempt | None:
    try:
        return limiter.begin_login(VICTIM, ip)
    except TooManyAttemptsError:
        return None
