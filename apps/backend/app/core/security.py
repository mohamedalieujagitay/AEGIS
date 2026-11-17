"""Password hashing and secret tokens (DECISIONS.md D-062, D-064).

- Passwords are hashed with Argon2id, RFC 9106 low-memory profile (64 MiB,
  3 iterations, 4 lanes). At most ``password_hash_concurrency`` hashes run at
  once, so concurrent sign-ins cannot exhaust the container's memory.
- Session and reset tokens are 256-bit random values. Only their SHA-256
  hash is stored; a fast hash is sufficient for random values of this size.
- Keyed hashes (HMAC-SHA-256 with the server secret) name rate-limit
  counters, so email addresses and client addresses never appear in Valkey.
"""

import hashlib
import hmac
import secrets
import threading
from typing import Final

from argon2 import PasswordHasher, profiles
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

TOKEN_BYTES: Final = 32

_hasher: Final = PasswordHasher.from_parameters(profiles.RFC_9106_LOW_MEMORY)
_slots = threading.BoundedSemaphore(4)
_dummy_hash: str | None = None
_dummy_lock = threading.Lock()


def configure_password_hashing(concurrency: int) -> None:
    """Set how many hashes may run at the same time, and prepare the dummy hash.

    The dummy hash is computed here, at start-up, so the first sign-in for an
    unknown account takes as long as every later one (DECISIONS.md D-062).
    """
    global _slots
    _slots = threading.BoundedSemaphore(concurrency)
    _ensure_dummy_hash()


def _ensure_dummy_hash() -> str:
    global _dummy_hash
    with _dummy_lock:
        if _dummy_hash is None:
            _dummy_hash = hash_password(secrets.token_urlsafe(16))
        return _dummy_hash


def hash_password(password: str) -> str:
    with _slots:
        return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Whether ``password`` matches. Malformed hashes never match."""
    try:
        with _slots:
            return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    """Whether the hash uses older parameters and should be replaced at sign-in."""
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True


def burn_password_check(password: str) -> None:
    """Spend the same time as a real verification, for unknown accounts.

    Without this, a sign-in attempt for an unknown email address would
    return measurably faster and reveal that the account does not exist.
    """
    verify_password(_ensure_dummy_hash(), password)


def new_token() -> str:
    """A new random token (256 bits, URL-safe)."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> str:
    """The stored form of a token: SHA-256, hexadecimal."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def keyed_hash(secret: bytes, value: str) -> str:
    """HMAC-SHA-256 of ``value``, hexadecimal, for names that must not reveal the value."""
    return hmac.new(secret, value.encode("utf-8"), hashlib.sha256).hexdigest()
