"""Authentication API: registration, sign-in, sessions, sign-out, reset, administration.

These tests run the real application on a migrated PostgreSQL database. Only
the rate-limit counters are kept in memory (``MemoryRateLimitStore``); the
Valkey store is exercised by the smoke test against the real stack.
"""

import hashlib
import logging
import threading
import uuid
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from http.cookies import SimpleCookie

import pytest
import redis
from fastapi import FastAPI
from helpers import TEST_SECRET_KEY, AegisTestClient, FakeClock
from httpx2 import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.csrf import ANONYMOUS_BINDING, csrf_binding, verify_csrf_token
from app.core.security import hash_password
from app.models.password_reset import PasswordResetToken
from app.models.session import UserSession
from app.models.user import User
from app.services import accounts, password_reset

PASSWORD = "correct horse battery staple"
NEW_PASSWORD = "a completely different passphrase"
AUTH = "/api/v1/auth"
SESSION_COOKIE = "__Host-aegis_session"
CSRF_COOKIE = "__Host-aegis_csrf"
DEVICE_COOKIE = "__Host-aegis_device"


# --- helpers --------------------------------------------------------------


@pytest.fixture
def db(auth_app: FastAPI) -> Iterator[Session]:
    with auth_app.state.database.session() as session:
        yield session


def make_user(
    app: FastAPI,
    email: str = "alice@example.com",
    username: str = "alice",
    *,
    admin: bool = False,
    password: str = PASSWORD,
) -> User:
    with app.state.database.session() as session:
        return accounts.create_account(
            session, email=email, username=username, password=password, instance_admin=admin
        )


def sign_in(
    app: FastAPI, email: str = "alice@example.com", password: str = PASSWORD
) -> AegisTestClient:
    client = AegisTestClient(app)
    response = client.post(f"{AUTH}/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return client


def set_cookies(response: Response) -> dict[str, SimpleCookie]:
    cookies = {}
    for header in response.headers.get_list("set-cookie"):
        cookie: SimpleCookie = SimpleCookie()
        cookie.load(header)
        [name] = cookie.keys()
        cookies[name] = cookie
    return cookies


def assert_secure_cookie(cookie: SimpleCookie, name: str, *, persistent: bool = False) -> None:
    morsel = cookie[name]
    assert morsel["httponly"] is True
    assert morsel["secure"] is True
    assert morsel["samesite"].lower() == "strict"
    assert morsel["path"] == "/"
    assert not morsel["domain"]
    if not persistent:
        # A browser-session cookie: the server enforces the real expiry.
        assert not morsel["max-age"]
    assert not morsel["expires"]


def session_rows(db: Session) -> list[UserSession]:
    db.expire_all()
    return list(db.scalars(select(UserSession).order_by(UserSession.created_at)))


def enable_registration(app: FastAPI) -> None:
    with app.state.database.session() as session:
        accounts.set_registration_enabled(session, True)


# --- CSRF token endpoint and options ---------------------------------------


def test_csrf_endpoint_issues_an_anonymous_token(auth_app: FastAPI, clock: FakeClock) -> None:
    response = AegisTestClient(auth_app).get(f"{AUTH}/csrf")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    token = response.json()["csrf_token"]
    cookies = set_cookies(response)
    assert_secure_cookie(cookies[CSRF_COOKIE], CSRF_COOKIE)
    assert cookies[CSRF_COOKIE][CSRF_COOKIE].value == token
    now = int(clock().timestamp())
    assert verify_csrf_token(TEST_SECRET_KEY.encode(), token, ANONYMOUS_BINDING, now, 60)


def test_options_are_public(auth_app: FastAPI) -> None:
    response = AegisTestClient(auth_app).get(f"{AUTH}/options")
    assert response.json() == {
        "registration_enabled": False,
        "session_idle_timeout_minutes": 60,
        "session_absolute_timeout_hours": 12,
    }


# --- sign-in ----------------------------------------------------------------


def test_login_creates_a_session_with_secure_cookies(
    auth_app: FastAPI, db: Session, clock: FakeClock
) -> None:
    make_user(auth_app)
    client = AegisTestClient(auth_app)
    response = client.post(
        f"{AUTH}/login",
        json={"email": " Alice@Example.com ", "password": PASSWORD},
        headers={"User-Agent": "pytest-browser"},
    )
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["user"]["username"] == "alice"
    assert body["user"]["is_instance_admin"] is False

    cookies = set_cookies(response)
    assert set(cookies) == {SESSION_COOKIE, CSRF_COOKIE, DEVICE_COOKIE}
    for name in (SESSION_COOKIE, CSRF_COOKIE):
        assert_secure_cookie(cookies[name], name)
    assert_secure_cookie(cookies[DEVICE_COOKIE], DEVICE_COOKIE, persistent=True)
    # The device cookie is the only persistent one: it lasts 30 days (D-070).
    assert cookies[DEVICE_COOKIE][DEVICE_COOKIE]["max-age"] == str(30 * 86400)
    session_token = cookies[SESSION_COOKIE][SESSION_COOKIE].value
    assert session_token not in response.text

    # Only the hash of the token is stored.
    [row] = session_rows(db)
    assert row.token_hash == hashlib.sha256(session_token.encode()).hexdigest()
    assert row.user_agent == "pytest-browser"
    assert row.expires_at == clock() + (row.expires_at - row.created_at)
    assert (row.expires_at - row.created_at).total_seconds() == 12 * 3600

    # The CSRF token is rotated: it is bound to the new session.
    now = int(clock().timestamp())
    assert verify_csrf_token(
        TEST_SECRET_KEY.encode(), body["csrf_token"], csrf_binding(session_token), now, 60
    )
    assert client.get(f"{AUTH}/me").json()["email"] == "alice@example.com"


def test_failed_sign_in_does_not_reveal_whether_the_account_exists(
    auth_app: FastAPI,
) -> None:
    make_user(auth_app)
    client = AegisTestClient(auth_app)
    wrong_password = client.post(
        f"{AUTH}/login", json={"email": "alice@example.com", "password": "wrong password!"}
    )
    unknown = client.post(
        f"{AUTH}/login", json={"email": "nobody@example.com", "password": PASSWORD}
    )
    invalid = client.post(f"{AUTH}/login", json={"email": "not-an-email", "password": PASSWORD})
    for response in (wrong_password, unknown, invalid):
        assert response.status_code == 401
        body = response.json()
        assert body["error"]["code"] == "invalid_credentials"
        assert SESSION_COOKIE not in response.headers.get("set-cookie", "")
    assert wrong_password.json()["error"]["message"] == unknown.json()["error"]["message"]


def test_deactivated_accounts_cannot_sign_in(auth_app: FastAPI, db: Session) -> None:
    user = make_user(auth_app)
    client = sign_in(auth_app)
    db.get_one(User, user.id).is_active = False
    db.commit()
    assert client.get(f"{AUTH}/me").status_code == 401
    response = AegisTestClient(auth_app).post(
        f"{AUTH}/login", json={"email": "alice@example.com", "password": PASSWORD}
    )
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_signing_in_again_replaces_the_previous_session(auth_app: FastAPI, db: Session) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)
    first = client.session_cookie()
    client.post(f"{AUTH}/login", json={"email": "alice@example.com", "password": PASSWORD})
    assert client.session_cookie() != first
    old, new = session_rows(db)
    assert old.revoked_reason == "replaced"
    assert new.revoked_at is None


# --- authentication required ------------------------------------------------


def test_protected_endpoints_require_a_session(auth_app: FastAPI) -> None:
    client = AegisTestClient(auth_app)
    response = client.get(f"{AUTH}/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_required"
    client.set_cookie(SESSION_COOKIE, "forged-session-token-value")
    assert client.get(f"{AUTH}/me").json()["error"]["code"] == "authentication_required"


def test_administration_requires_an_instance_administrator(auth_app: FastAPI) -> None:
    make_user(auth_app)
    anonymous = AegisTestClient(auth_app)
    user = sign_in(auth_app)
    for client, status in ((anonymous, 401), (user, 403)):
        assert client.get("/api/v1/admin/settings/registration").status_code == status
        assert (
            client.put("/api/v1/admin/settings/registration", json={"enabled": True}).status_code
            == status
        )
        assert (
            client.post(
                "/api/v1/admin/password-resets", json={"email": "alice@example.com"}
            ).status_code
            == status
        )


# --- sessions: expiry and revocation ----------------------------------------


def test_idle_sessions_expire(auth_app: FastAPI, clock: FakeClock) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)
    clock.advance(minutes=59)
    assert client.get(f"{AUTH}/me").status_code == 200  # activity extends the session
    clock.advance(minutes=59)
    assert client.get(f"{AUTH}/me").status_code == 200
    clock.advance(minutes=60)
    response = client.get(f"{AUTH}/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "session_expired"


def test_sessions_have_an_absolute_lifetime(auth_app: FastAPI, clock: FakeClock) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)
    for _ in range(14):  # active every 50 minutes for 11 h 40 min
        clock.advance(minutes=50)
        assert client.get(f"{AUTH}/me").status_code == 200
    clock.advance(minutes=20)
    assert client.get(f"{AUTH}/me").json()["error"]["code"] == "session_expired"


def test_logout_revokes_the_session_on_the_server(auth_app: FastAPI, db: Session) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)
    stolen = client.session_cookie()
    response = client.post(f"{AUTH}/logout")
    assert response.status_code == 204
    cleared = set_cookies(response)
    for name in (SESSION_COOKIE, CSRF_COOKIE):
        assert cleared[name][name].value == ""
        assert cleared[name][name]["max-age"] == "0"
    [row] = session_rows(db)
    assert row.revoked_reason == "logout"

    # Replaying the old cookie does not work.
    replay = AegisTestClient(auth_app)
    replay.set_cookie(SESSION_COOKIE, stolen or "")
    assert replay.get(f"{AUTH}/me").status_code == 401


def test_logout_without_a_session_succeeds(auth_app: FastAPI) -> None:
    assert AegisTestClient(auth_app).post(f"{AUTH}/logout").status_code == 204


# --- registration -------------------------------------------------------------


def test_a_registration_setting_change_is_seen_by_the_next_request(auth_app: FastAPI) -> None:
    """The browser tests enable registration and read it at once (commit before response)."""
    make_user(auth_app, "admin@example.com", "admin", admin=True)
    administrator = sign_in(auth_app, "admin@example.com")
    visitor = AegisTestClient(auth_app)
    assert visitor.get(f"{AUTH}/options").json()["registration_enabled"] is False

    for enabled in (True, False, True):
        response = administrator.put(
            "/api/v1/admin/settings/registration", json={"enabled": enabled}
        )
        assert response.status_code == 200
        assert visitor.get(f"{AUTH}/options").json()["registration_enabled"] is enabled


def test_registration_is_disabled_by_default(auth_app: FastAPI, db: Session) -> None:
    response = AegisTestClient(auth_app).post(
        f"{AUTH}/register",
        json={"email": "new@example.com", "username": "newuser", "password": PASSWORD},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "registration_disabled"
    assert db.scalars(select(User)).all() == []


def test_registration_creates_an_account_and_signs_in(auth_app: FastAPI, db: Session) -> None:
    enable_registration(auth_app)
    client = AegisTestClient(auth_app)
    response = client.post(
        f"{AUTH}/register",
        json={"email": "New@Example.com", "username": "NewUser", "password": PASSWORD},
    )
    assert response.status_code == 201
    assert response.json()["user"] == {
        "id": response.json()["user"]["id"],
        "email": "new@example.com",
        "username": "newuser",
        "is_instance_admin": False,
    }
    assert_secure_cookie(set_cookies(response)[SESSION_COOKIE], SESSION_COOKIE)
    assert client.get(f"{AUTH}/me").status_code == 200
    user = db.scalars(select(User)).one()
    assert user.password_hash.startswith("$argon2id$")
    assert PASSWORD not in user.password_hash


@pytest.mark.parametrize(
    "duplicate",
    [
        {"email": "ALICE@example.com", "username": "someone"},
        {"email": "someone@example.com", "username": "Alice"},
    ],
)
def test_duplicate_registration_is_refused_generically(
    auth_app: FastAPI, duplicate: dict[str, str]
) -> None:
    make_user(auth_app)
    enable_registration(auth_app)
    response = AegisTestClient(auth_app).post(
        f"{AUTH}/register", json={**duplicate, "password": PASSWORD}
    )
    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "registration_rejected"
    assert "email" not in error["message"].lower() or "username" in error["message"].lower()


@pytest.mark.parametrize(
    ("payload", "status", "code"),
    [
        ({"email": "bad", "username": "newuser", "password": PASSWORD}, 422, "validation_error"),
        (
            {"email": "n@example.com", "username": "x", "password": PASSWORD},
            422,
            "validation_error",
        ),
        (
            {"email": "n@example.com", "username": "newuser", "password": "short"},
            422,
            "password_rejected",
        ),
        (
            {"email": "n@example.com", "username": "newuser", "password": "newuser-password-1"},
            422,
            "password_rejected",
        ),
        (
            {"email": "n@example.com", "username": "newuser", "password": "p" * 129},
            422,
            "validation_error",
        ),
    ],
)
def test_registration_validates_its_input(
    auth_app: FastAPI, db: Session, payload: dict[str, str], status: int, code: str
) -> None:
    enable_registration(auth_app)
    response = AegisTestClient(auth_app).post(f"{AUTH}/register", json=payload)
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert payload["password"] not in response.text
    assert db.scalars(select(User)).all() == []


def test_admin_can_toggle_registration(auth_app: FastAPI) -> None:
    make_user(auth_app, admin=True)
    admin = sign_in(auth_app)
    url = "/api/v1/admin/settings/registration"
    assert admin.get(url).json() == {"enabled": False}
    assert admin.put(url, json={"enabled": True}).json() == {"enabled": True}
    assert AegisTestClient(auth_app).get(f"{AUTH}/options").json()["registration_enabled"]
    assert admin.put(url, json={"enabled": False}).json() == {"enabled": False}


# --- password reset -------------------------------------------------------------


def issue_reset(app: FastAPI, email: str = "alice@example.com") -> str:
    make_user(app, "admin@example.com", "admin", admin=True)
    admin = sign_in(app, "admin@example.com")
    response = admin.post("/api/v1/admin/password-resets", json={"email": email})
    assert response.status_code == 201, response.text
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["reset_path"] == f"/reset-password#token={body['reset_token']}"
    token: str = body["reset_token"]
    return token


def test_password_reset_flow(auth_app: FastAPI, db: Session) -> None:
    make_user(auth_app)
    alice = sign_in(auth_app)
    token = issue_reset(auth_app)
    stored = db.scalars(select(PasswordResetToken)).one()
    assert stored.token_hash == hashlib.sha256(token.encode()).hexdigest()

    anonymous = AegisTestClient(auth_app)
    response = anonymous.post(
        f"{AUTH}/password/reset", json={"token": token, "new_password": NEW_PASSWORD}
    )
    assert response.status_code == 204
    # No automatic sign-in after a reset; cookies are cleared.
    assert all(c[n].value == "" for n, c in set_cookies(response).items())

    # Every existing session was revoked.
    assert alice.get(f"{AUTH}/me").status_code == 401
    # The old password no longer works; the new one does.
    old = anonymous.post(f"{AUTH}/login", json={"email": "alice@example.com", "password": PASSWORD})
    assert old.status_code == 401
    sign_in(auth_app, password=NEW_PASSWORD)

    # Tokens are single-use.
    again = anonymous.post(
        f"{AUTH}/password/reset", json={"token": token, "new_password": "yet another passphrase"}
    )
    assert again.status_code == 400
    assert again.json()["error"]["code"] == "invalid_reset_token"


def test_reset_tokens_expire(auth_app: FastAPI, clock: FakeClock) -> None:
    make_user(auth_app)
    token = issue_reset(auth_app)
    clock.advance(minutes=60)
    response = AegisTestClient(auth_app).post(
        f"{AUTH}/password/reset", json={"token": token, "new_password": NEW_PASSWORD}
    )
    assert response.json()["error"]["code"] == "invalid_reset_token"


def test_issuing_a_new_token_invalidates_the_previous_one(auth_app: FastAPI) -> None:
    make_user(auth_app)
    first = issue_reset(auth_app)
    admin = sign_in(auth_app, "admin@example.com")
    second = admin.post("/api/v1/admin/password-resets", json={"email": "alice@example.com"})
    client = AegisTestClient(auth_app)
    reset = f"{AUTH}/password/reset"
    stale = client.post(reset, json={"token": first, "new_password": NEW_PASSWORD})
    assert stale.status_code == 400
    fresh = client.post(
        reset, json={"token": second.json()["reset_token"], "new_password": NEW_PASSWORD}
    )
    assert fresh.status_code == 204


def test_a_rejected_new_password_keeps_the_token_usable(auth_app: FastAPI) -> None:
    make_user(auth_app)
    token = issue_reset(auth_app)
    client = AegisTestClient(auth_app)
    weak = client.post(f"{AUTH}/password/reset", json={"token": token, "new_password": "short"})
    assert weak.json()["error"]["code"] == "password_rejected"
    ok = client.post(f"{AUTH}/password/reset", json={"token": token, "new_password": NEW_PASSWORD})
    assert ok.status_code == 204


def test_unknown_reset_tokens_are_refused(auth_app: FastAPI) -> None:
    response = AegisTestClient(auth_app).post(
        f"{AUTH}/password/reset",
        json={"token": "A" * 43, "new_password": NEW_PASSWORD},
    )
    assert response.json()["error"]["code"] == "invalid_reset_token"


def test_issuing_a_reset_for_an_unknown_user(auth_app: FastAPI) -> None:
    make_user(auth_app, "admin@example.com", "admin", admin=True)
    admin = sign_in(auth_app, "admin@example.com")
    response = admin.post("/api/v1/admin/password-resets", json={"email": "ghost@example.com"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"


# --- CSRF -------------------------------------------------------------------------


def _login_without_csrf(app: FastAPI, **headers: str) -> Response:
    client = AegisTestClient(app, auto_csrf=False)
    return client.post(
        f"{AUTH}/login",
        json={"email": "alice@example.com", "password": PASSWORD},
        headers=headers,
    )


def test_login_requires_a_csrf_token(auth_app: FastAPI) -> None:
    """Login CSRF: another site cannot sign the browser in to an attacker's account."""
    make_user(auth_app)
    response = _login_without_csrf(auth_app)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_failed"


def test_header_must_match_the_cookie(auth_app: FastAPI) -> None:
    make_user(auth_app)
    client = AegisTestClient(auth_app, auto_csrf=False)
    valid = client.csrf_token()
    other = AegisTestClient(auth_app).csrf_token()
    response = client.post(
        f"{AUTH}/login",
        json={"email": "alice@example.com", "password": PASSWORD},
        headers={"X-CSRF-Token": other},
    )
    assert response.status_code == 403
    assert valid != other


@pytest.mark.parametrize("token", ["garbage", "v1.1.nonce.signature"])
def test_invalid_tokens_are_refused(auth_app: FastAPI, token: str) -> None:
    client = AegisTestClient(auth_app, auto_csrf=False)
    client.set_cookie(CSRF_COOKIE, token)
    response = client.post(f"{AUTH}/logout", headers={"X-CSRF-Token": token})
    assert response.status_code == 403


def test_a_token_from_another_session_is_refused(auth_app: FastAPI) -> None:
    make_user(auth_app)
    make_user(auth_app, "bob@example.com", "bob")
    alice = sign_in(auth_app)
    bob = sign_in(auth_app, "bob@example.com")
    alice_token = alice.csrf_token()
    bob.auto_csrf = False
    bob.set_cookie(CSRF_COOKIE, alice_token)
    response = bob.post(f"{AUTH}/logout", headers={"X-CSRF-Token": alice_token})
    assert response.status_code == 403
    assert bob.get(f"{AUTH}/me").status_code == 200


def test_tokens_are_rotated_at_sign_in_and_sign_out(auth_app: FastAPI) -> None:
    make_user(auth_app)
    client = AegisTestClient(auth_app, auto_csrf=False)
    anonymous = client.get(f"{AUTH}/csrf").json()["csrf_token"]
    login = client.post(
        f"{AUTH}/login",
        json={"email": "alice@example.com", "password": PASSWORD},
        headers={"X-CSRF-Token": anonymous},
    )
    assert login.status_code == 200
    session_token = login.json()["csrf_token"]
    assert session_token != anonymous

    # The anonymous token stops working once a session exists.
    client.set_cookie(CSRF_COOKIE, anonymous)
    assert client.post(f"{AUTH}/logout", headers={"X-CSRF-Token": anonymous}).status_code == 403

    client.set_cookie(CSRF_COOKIE, session_token)
    assert client.post(f"{AUTH}/logout", headers={"X-CSRF-Token": session_token}).status_code == 204

    # After sign-out the session token is useless, even with its cookie restored.
    client.set_cookie(CSRF_COOKIE, session_token)
    response = client.post(
        f"{AUTH}/login",
        json={"email": "alice@example.com", "password": PASSWORD},
        headers={"X-CSRF-Token": session_token},
    )
    assert response.status_code == 403


def test_tokens_expire(auth_app: FastAPI, clock: FakeClock) -> None:
    client = AegisTestClient(auth_app, auto_csrf=False)
    token = client.get(f"{AUTH}/csrf").json()["csrf_token"]
    clock.advance(hours=12, seconds=1)
    assert client.post(f"{AUTH}/logout", headers={"X-CSRF-Token": token}).status_code == 403


@pytest.mark.parametrize(
    "headers",
    [
        {"Origin": "https://evil.example"},
        {"Origin": "null"},
        {"Origin": "http://testserver"},  # same host, different scheme
        {"Sec-Fetch-Site": "cross-site"},
    ],
)
def test_cross_origin_requests_are_refused_even_with_a_valid_token(
    auth_app: FastAPI, headers: dict[str, str]
) -> None:
    make_user(auth_app)
    client = AegisTestClient(auth_app)
    response = client.post(
        f"{AUTH}/login",
        json={"email": "alice@example.com", "password": PASSWORD},
        headers=headers,
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_failed"


@pytest.mark.parametrize(
    "headers",
    [{"Origin": "https://testserver"}, {"Sec-Fetch-Site": "same-origin"}, {}],
)
def test_same_origin_requests_are_accepted(auth_app: FastAPI, headers: dict[str, str]) -> None:
    make_user(auth_app)
    client = AegisTestClient(auth_app)
    response = client.post(
        f"{AUTH}/login",
        json={"email": "alice@example.com", "password": PASSWORD},
        headers=headers,
    )
    assert response.status_code == 200


def test_configured_origins_are_accepted(make_auth_app: Callable[..., FastAPI]) -> None:
    client = AegisTestClient(make_auth_app(allowed_origins="http://localhost:5173"))
    allowed = client.post(f"{AUTH}/logout", headers={"Origin": "http://localhost:5173"})
    assert allowed.status_code == 204
    other = client.post(f"{AUTH}/logout", headers={"Origin": "http://localhost:5174"})
    assert other.status_code == 403


def test_safe_methods_are_not_checked(auth_app: FastAPI) -> None:
    client = AegisTestClient(auth_app, auto_csrf=False)
    assert (
        client.get(f"{AUTH}/options", headers={"Origin": "https://evil.example"}).status_code == 200
    )


# --- rate limiting through the API ------------------------------------------------


def test_repeated_failures_are_throttled(auth_app: FastAPI, clock: FakeClock) -> None:
    make_user(auth_app)
    client = AegisTestClient(auth_app)
    wrong = {"email": "alice@example.com", "password": "wrong password!"}
    for _ in range(6):
        assert client.post(f"{AUTH}/login", json=wrong).status_code == 401
    throttled = client.post(
        f"{AUTH}/login", json={"email": "alice@example.com", "password": PASSWORD}
    )
    assert throttled.status_code == 429
    assert throttled.headers["retry-after"] == "30"
    assert throttled.json()["error"]["code"] == "too_many_requests"

    # Unknown accounts are throttled the same way (no enumeration).
    for _ in range(6):
        client.post(f"{AUTH}/login", json={"email": "ghost@example.com", "password": "x"})
    ghost = client.post(f"{AUTH}/login", json={"email": "ghost@example.com", "password": "x"})
    assert ghost.status_code == 429
    assert ghost.json() | {"error": None} == throttled.json() | {"error": None}

    clock.advance(seconds=30)
    sign_in(auth_app)


def test_registration_attempts_are_limited(auth_app: FastAPI) -> None:
    client = AegisTestClient(auth_app)
    payload = {"email": "n@example.com", "username": "newuser", "password": PASSWORD}
    for _ in range(5):
        assert client.post(f"{AUTH}/register", json=payload).status_code == 403
    assert client.post(f"{AUTH}/register", json=payload).status_code == 429


def test_reset_attempts_are_limited(auth_app: FastAPI) -> None:
    client = AegisTestClient(auth_app)
    payload = {"token": "A" * 43, "new_password": NEW_PASSWORD}
    for _ in range(10):
        assert client.post(f"{AUTH}/password/reset", json=payload).status_code == 400
    assert client.post(f"{AUTH}/password/reset", json=payload).status_code == 429


def test_rate_limiter_outage_fails_closed(auth_app: FastAPI) -> None:
    make_user(auth_app)
    auth_app.state.auth.limiter._store.fail_with = redis.ConnectionError("down")
    client = AegisTestClient(auth_app)
    for url, payload in (
        (f"{AUTH}/login", {"email": "alice@example.com", "password": PASSWORD}),
        (f"{AUTH}/register", {"email": "n@example.com", "username": "nn1", "password": PASSWORD}),
        (f"{AUTH}/password/reset", {"token": "A" * 43, "new_password": NEW_PASSWORD}),
    ):
        response = client.post(url, json=payload)
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "service_unavailable"


# --- security logging ----------------------------------------------------------------


def test_security_events_never_contain_secrets(
    auth_app: FastAPI,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    make_user(auth_app)
    with caplog.at_level(logging.DEBUG):
        alice = sign_in(auth_app)
        session_token = alice.session_cookie() or ""
        csrf_token = alice.csrf_token()
        AegisTestClient(auth_app).post(
            f"{AUTH}/login", json={"email": "alice@example.com", "password": "wrong password!"}
        )
        reset_token = issue_reset(auth_app)
        AegisTestClient(auth_app).post(
            f"{AUTH}/password/reset", json={"token": reset_token, "new_password": NEW_PASSWORD}
        )
        AegisTestClient(auth_app, auto_csrf=False).post(f"{AUTH}/logout")
    output = caplog.text + capsys.readouterr().out
    events = {getattr(r, "event", None) for r in caplog.records}
    assert {
        "auth.login_succeeded",
        "auth.login_failed",
        "auth.password_reset_issued",
        "auth.password_reset_completed",
        "auth.csrf_rejected",
    } <= events
    for secret in (
        PASSWORD,
        NEW_PASSWORD,
        "wrong password!",
        session_token,
        csrf_token,
        reset_token,
        TEST_SECRET_KEY,
    ):
        assert secret not in output
    for record in caplog.records:
        assert "alice@example.com" not in str(record.__dict__)


# --- Remediation tests (DECISIONS.md D-070, D-071, D-072) ----------------------


def test_owner_with_a_device_token_signs_in_during_a_distributed_attack(
    make_auth_app: Callable[..., FastAPI], clock: FakeClock
) -> None:
    """End to end over HTTP: the attack from rotating addresses does not lock the owner out."""
    app = make_auth_app()
    make_user(app)
    owner = AegisTestClient(app, client=("198.51.100.7", 50000))
    assert (
        owner.post(
            f"{AUTH}/login", json={"email": "alice@example.com", "password": PASSWORD}
        ).status_code
        == 200
    )
    assert owner.post(f"{AUTH}/logout").status_code == 204  # the device cookie remains

    for index in range(21):  # the account-wide threshold, from 21 addresses
        attacker = AegisTestClient(app, client=(f"203.0.113.{index}", 50000))
        status = attacker.post(
            f"{AUTH}/login", json={"email": "alice@example.com", "password": "wrong password!"}
        ).status_code
        assert status in (401, 429)

    owner_results: list[int] = []
    stranger_results: list[int] = []
    for _ in range(30):
        clock.advance(seconds=1)
        attacker = AegisTestClient(app, client=("203.0.113.99", 50000))
        attacker.post(
            f"{AUTH}/login", json={"email": "alice@example.com", "password": "wrong password!"}
        )
        owner_results.append(
            owner.post(
                f"{AUTH}/login", json={"email": "alice@example.com", "password": PASSWORD}
            ).status_code
        )
        owner.post(f"{AUTH}/logout")
        # A browser without the device token, from the owner's own address.
        stranger = AegisTestClient(app, client=("198.51.100.7", 50001))
        stranger_results.append(
            stranger.post(
                f"{AUTH}/login", json={"email": "alice@example.com", "password": PASSWORD}
            ).status_code
        )
    assert owner_results == [200] * 30
    # The residual risk is documented (SR-009): without the token the owner waits.
    assert 429 in stranger_results


def test_a_forged_device_cookie_gets_no_exemption(
    make_auth_app: Callable[..., FastAPI],
) -> None:
    app = make_auth_app()
    make_user(app)
    for index in range(21):  # the account-wide delay is now in force
        AegisTestClient(app, client=(f"203.0.113.{index}", 50000)).post(
            f"{AUTH}/login", json={"email": "alice@example.com", "password": "wrong password!"}
        )
    forged = AegisTestClient(app, client=("198.51.100.7", 50000))
    forged.set_cookie("__Host-aegis_device", f"v1.{uuid.uuid4()}.1.forged.signature")
    response = forged.post(
        f"{AUTH}/login", json={"email": "alice@example.com", "password": PASSWORD}
    )
    assert response.status_code == 429


def test_a_password_reset_clears_the_device_cookie(auth_app: FastAPI) -> None:
    make_user(auth_app)
    token = issue_reset(auth_app)
    response = AegisTestClient(auth_app).post(
        f"{AUTH}/password/reset", json={"token": token, "new_password": NEW_PASSWORD}
    )
    assert response.status_code == 204
    cleared = set_cookies(response)
    assert cleared["__Host-aegis_device"]["__Host-aegis_device"]["max-age"] == "0"


@pytest.mark.parametrize(
    "email",
    ["User@Bücher.example", "user@BÜCHER.EXAMPLE", "user@xn--bcher-kva.example"],
)
def test_international_addresses_sign_in_in_every_spelling(auth_app: FastAPI, email: str) -> None:
    enable_registration(auth_app)
    assert (
        AegisTestClient(auth_app)
        .post(
            f"{AUTH}/register",
            json={"email": "User@Bücher.example", "username": "bucher", "password": PASSWORD},
        )
        .status_code
        == 201
    )
    client = AegisTestClient(auth_app)
    client.post(f"{AUTH}/logout")
    response = client.post(f"{AUTH}/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200


@pytest.mark.parametrize(
    "email",
    [
        "",
        "nope",
        "a@b@c",
        "@",
        "user@\u0000.example",
        "🙂@🙂.example",
        "x" * 300,
        "user@" + "é" * 200,
    ],
)
def test_malformed_sign_in_addresses_fail_safely(auth_app: FastAPI, email: str) -> None:
    response = AegisTestClient(auth_app).post(
        f"{AUTH}/login", json={"email": email, "password": PASSWORD}
    )
    assert response.status_code in (401, 422)
    assert response.status_code != 500
    assert response.json()["error"]["code"] in ("invalid_credentials", "validation_error")


def insert_user_directly(app: FastAPI, email: str) -> None:
    with app.state.database.session() as db:
        db.add(
            User(
                id=uuid.uuid4(),
                email=email,
                username="upper",
                password_hash=hash_password(PASSWORD),
            )
        )
        db.flush()


def test_database_rejects_a_non_normalized_email(auth_app: FastAPI) -> None:
    from sqlalchemy.exc import IntegrityError

    # Written directly, bypassing the application's normalization, to test the database.
    with pytest.raises(IntegrityError, match="ck_users_email_normalized"):
        insert_user_directly(auth_app, "Upper@example.com")


def test_two_concurrent_redemptions_of_one_reset_token_admit_exactly_one(
    make_auth_app: Callable[..., FastAPI], clock: FakeClock
) -> None:
    """Row locking: the token is consumed once, even when two requests race."""
    app = make_auth_app()
    make_user(app)
    token = issue_reset(app)
    barrier = threading.Barrier(2)

    def redeem() -> str:
        barrier.wait()
        try:
            with app.state.database.session() as db:
                password_reset.redeem_reset_token(db, token, NEW_PASSWORD, clock())
        except password_reset.InvalidResetTokenError:
            return "refused"
        return "accepted"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(lambda _: redeem(), range(2)))
    assert outcomes == ["accepted", "refused"]
