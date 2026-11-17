"""Unit tests for password hashing, tokens, identifiers, CSRF tokens and settings."""

import hashlib
import logging

import pytest
from argon2 import PasswordHasher
from pydantic import SecretStr, ValidationError

from app.core.config import Environment, Settings
from app.core.csrf import (
    ANONYMOUS_BINDING,
    csrf_binding,
    issue_csrf_token,
    verify_csrf_token,
)
from app.core.identity import normalize_email, normalize_username, password_problems
from app.core.security import (
    hash_password,
    hash_token,
    keyed_hash,
    new_token,
    password_needs_rehash,
    verify_password,
)
from app.main import create_app

SECRET = b"s" * 32
NOW = 1_800_000_000


# --- Argon2id -------------------------------------------------------------


def test_passwords_are_hashed_with_argon2id_rfc_9106_low_memory() -> None:
    hashed = hash_password("correct horse battery staple")
    assert hashed.startswith("$argon2id$v=19$m=65536,t=3,p=4$")
    assert "correct horse" not in hashed
    assert hash_password("correct horse battery staple") != hashed  # random salt


def test_verification() -> None:
    hashed = hash_password("correct horse battery staple")
    assert verify_password(hashed, "correct horse battery staple")
    assert not verify_password(hashed, "correct horse battery stapl")
    assert not verify_password("not-a-hash", "anything")


def test_weaker_hashes_are_upgraded() -> None:
    old = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1).hash("pw")
    assert verify_password(old, "pw")
    assert password_needs_rehash(old)
    assert not password_needs_rehash(hash_password("pw"))


# --- Tokens ---------------------------------------------------------------


def test_tokens_are_random_and_stored_as_sha256() -> None:
    token = new_token()
    assert len(token) == 43  # 256 bits, base64url
    assert token != new_token()
    assert hash_token(token) == hashlib.sha256(token.encode()).hexdigest()


def test_keyed_hash_depends_on_the_secret() -> None:
    assert keyed_hash(SECRET, "a") != keyed_hash(b"t" * 32, "a")
    assert keyed_hash(SECRET, "a") == keyed_hash(SECRET, "a")


# --- Identifiers and password policy --------------------------------------


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [
        ("  Alice@Example.COM ", "alice@example.com"),
        ("first.last+tag@sub.example.org", "first.last+tag@sub.example.org"),
        ("user@bücher.example", "user@xn--bcher-kva.example"),
    ],
)
def test_email_normalization(raw: str, normalized: str) -> None:
    assert normalize_email(raw) == normalized


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        "no-at-sign",
        "two@@example.com",
        "a@b@example.com",
        ".dot@example.com",
        "dot.@example.com",
        "do..ts@example.com",
        "user@localhost",
        "user@-bad.example",
        "user@exa mple.com",
        "us er@example.com",
        "x" * 65 + "@example.com",
        "user@" + "a" * 250 + ".com",
    ],
)
def test_invalid_email_addresses(invalid: str) -> None:
    with pytest.raises(ValueError, match="valid email"):
        normalize_email(invalid)


def test_usernames() -> None:
    assert normalize_username(" Alice.Smith_1 ") == "alice.smith_1"
    for invalid in ("ab", "a" * 33, "has space", "émile", "semi;colon"):
        with pytest.raises(ValueError, match="3 to 32"):
            normalize_username(invalid)


def test_password_policy() -> None:
    email, username = "alice@example.com", "alice"
    assert password_problems("correct horse battery staple", email=email, username=username) == []
    assert password_problems("short", email=email, username=username) == [
        "Use at least 12 characters."
    ]
    assert password_problems("x" * 129, email=email, username=username) == [
        "Use at most 128 characters."
    ]
    assert "Do not include your username." in password_problems(
        "my-ALICE-password-1", email=email, username=username
    )
    assert "Do not include your email address." in password_problems(
        "bobby-tables-2026", email="bobby@example.com", username="robert"
    )
    # No composition rules: a long passphrase of lowercase words is fine.
    assert password_problems(" spaces count too ", email=email, username=username) == []


# --- CSRF tokens ----------------------------------------------------------


def test_csrf_binding() -> None:
    assert csrf_binding(None) == ANONYMOUS_BINDING
    assert csrf_binding("") == ANONYMOUS_BINDING
    binding = csrf_binding("session-token")
    assert binding.startswith("session:")
    assert "session-token" not in binding


def test_csrf_tokens_are_bound_signed_and_expire() -> None:
    session = csrf_binding("session-a")
    token = issue_csrf_token(SECRET, session, NOW)
    assert verify_csrf_token(SECRET, token, session, NOW + 10, 3600)
    assert not verify_csrf_token(SECRET, token, csrf_binding("session-b"), NOW, 3600)
    assert not verify_csrf_token(SECRET, token, ANONYMOUS_BINDING, NOW, 3600)
    assert not verify_csrf_token(b"x" * 32, token, session, NOW, 3600)
    assert not verify_csrf_token(SECRET, token, session, NOW + 3601, 3600)
    assert not verify_csrf_token(SECRET, token, session, NOW - 1, 3600)  # issued in the future


@pytest.mark.parametrize(
    "tampered",
    [
        "",
        "garbage",
        "v1.abc.nonce.sig",
        "v2.{t}.nonce.sig",
        "{token}x",
        "{token}.extra",
    ],
)
def test_malformed_csrf_tokens_are_refused(tampered: str) -> None:
    token = issue_csrf_token(SECRET, ANONYMOUS_BINDING, NOW)
    value = tampered.format(t=NOW, token=token)
    assert not verify_csrf_token(SECRET, value, ANONYMOUS_BINDING, NOW, 3600)


def test_csrf_issue_time_cannot_be_changed() -> None:
    token = issue_csrf_token(SECRET, ANONYMOUS_BINDING, NOW)
    version, _, nonce, signature = token.split(".")
    forged = f"{version}.{NOW + 1000}.{nonce}.{signature}"
    assert not verify_csrf_token(SECRET, forged, ANONYMOUS_BINDING, NOW + 1000, 3600)


# --- Settings -------------------------------------------------------------


def test_secret_key_must_be_long_enough() -> None:
    with pytest.raises(ValidationError, match="at least 32"):
        Settings(secret_key=SecretStr("too-short"))


def test_configuration_errors_never_quote_secrets() -> None:
    with pytest.raises(ValidationError) as error:
        Settings(secret_key=SecretStr("sensitive-but-short"), environment=Environment.PRODUCTION)
    assert "sensitive" not in str(error.value)
    with pytest.raises(ValidationError) as error:
        Settings(
            secret_key=SecretStr("sensitive-value-long-enough-0123456789"), cookie_secure=False
        )
    assert "sensitive" not in str(error.value)


def test_production_requires_secure_cookies() -> None:
    with pytest.raises(ValidationError, match="AEGIS_COOKIE_SECURE"):
        Settings(environment=Environment.PRODUCTION, cookie_secure=False)
    assert Settings(environment=Environment.DEVELOPMENT, cookie_secure=False)


def test_cookie_names_use_the_host_prefix_when_secure() -> None:
    assert Settings().session_cookie_name == "__Host-aegis_session"
    assert Settings().csrf_cookie_name == "__Host-aegis_csrf"
    insecure = Settings(environment=Environment.DEVELOPMENT, cookie_secure=False)
    assert insecure.session_cookie_name == "aegis_session"


def test_allowed_origins_are_parsed() -> None:
    settings = Settings(allowed_origins=" http://a.example:8080/ ,https://b.example,, ")
    assert settings.allowed_origin_list == frozenset({"http://a.example:8080", "https://b.example"})


def test_production_requires_a_secret_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AEGIS_SECRET_KEY")
    with pytest.raises(RuntimeError, match="AEGIS_SECRET_KEY is required"):
        create_app(Settings())


def test_development_without_a_secret_key_uses_a_temporary_one(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.delenv("AEGIS_SECRET_KEY")
    with caplog.at_level(logging.WARNING, logger="app.main"):
        first = create_app(Settings(environment=Environment.DEVELOPMENT))
        second = create_app(Settings(environment=Environment.DEVELOPMENT))
    assert first.state.auth.secret != second.state.auth.secret
    assert len(first.state.auth.secret) == 32
    assert any(getattr(r, "event", None) == "auth.ephemeral_secret_key" for r in caplog.records)


# --- Email normalization shared by registration, sign-in and rate limits (D-071) ---


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("User@Bücher.example", "user@xn--bcher-kva.example"),
        ("user@BÜCHER.EXAMPLE", "user@xn--bcher-kva.example"),
        ("user@xn--bcher-kva.example", "user@xn--bcher-kva.example"),
        ("  Alice@Example.COM  ", "alice@example.com"),
    ],
)
def test_equivalent_spellings_normalize_to_one_address(raw: str, expected: str) -> None:
    from app.core.identity import normalize_email, normalize_email_for_lookup

    assert normalize_email(raw) == expected
    assert normalize_email_for_lookup(raw) == expected


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        "nope",
        "a@b@c",
        "@",
        "x" * 500,
        "user@\u0000.example",
        "🙂@🙂.example",
        "user@" + "é" * 300,
    ],
)
def test_lookup_normalization_never_raises(invalid: str) -> None:
    from app.core.identity import normalize_email_for_lookup

    assert isinstance(normalize_email_for_lookup(invalid), str)


def test_the_dummy_hash_is_prepared_when_hashing_is_configured() -> None:
    from app.core import security

    security.configure_password_hashing(4)
    assert security._dummy_hash is not None
    assert security._dummy_hash.startswith("$argon2id$")
