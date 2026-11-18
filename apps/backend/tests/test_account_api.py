"""Account management API (roadmap task 2.2): profile, password and sessions.

Covers ownership, CSRF, rate limiting, generic errors, the session rotation and
revocation rules, the trusted-device rule of D-070 and log hygiene.
"""

import logging
import threading
import time
from collections.abc import Iterator
from datetime import timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from helpers import COOKIE_DOMAIN, AegisTestClient
from sqlalchemy import select, text, update
from sqlalchemy.orm import Session
from test_auth_api import make_user, sign_in

from app.core import clock
from app.core.security import hash_token
from app.models.session import UserSession
from app.models.trusted_device import TrustedDevice
from app.models.user import User
from app.services import sessions, trusted_devices

PASSWORD = "correct horse battery staple"
NEW_PASSWORD = "a completely different passphrase"
ACCOUNT = "/api/v1/account"
AUTH = "/api/v1/auth"


@pytest.fixture
def db(auth_app: FastAPI) -> Iterator[Session]:
    with auth_app.state.database.session() as session:
        yield session


def user_by_name(db: Session, username: str) -> User:
    return db.scalars(select(User).where(User.username == username)).one()


def session_rows(db: Session, username: str) -> list[UserSession]:
    user = user_by_name(db, username)
    return list(db.scalars(select(UserSession).where(UserSession.user_id == user.id)).all())


# --- profile ----------------------------------------------------------------


def test_profile_shows_the_account_and_is_not_cached(auth_app: FastAPI) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)

    response = client.get(f"{ACCOUNT}/profile")

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert body["username"] == "alice"
    assert body["is_active"] is True
    assert "created_at" in body
    assert set(body) == {"email", "username", "created_at", "is_active"}
    assert response.headers["Cache-Control"] == "no-store"


def test_profile_requires_a_session(auth_app: FastAPI) -> None:
    make_user(auth_app)
    assert AegisTestClient(auth_app).get(f"{ACCOUNT}/profile").status_code == 401


def test_username_changes_with_the_current_password(auth_app: FastAPI, db: Session) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)

    response = client.patch(
        f"{ACCOUNT}/profile", json={"username": "Alice.Smith", "current_password": PASSWORD}
    )

    assert response.status_code == 200
    assert response.json()["username"] == "alice.smith"
    assert user_by_name(db, "alice.smith").email == "alice@example.com"
    assert client.get(f"{ACCOUNT}/profile").json()["username"] == "alice.smith"


def test_a_wrong_current_password_refuses_the_username_change(
    auth_app: FastAPI, db: Session
) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)

    response = client.patch(
        f"{ACCOUNT}/profile", json={"username": "newname", "current_password": "wrong one entirely"}
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "current_password_incorrect"
    assert user_by_name(db, "alice").username == "alice"


def test_a_taken_username_is_refused_without_naming_the_holder(auth_app: FastAPI) -> None:
    make_user(auth_app)
    make_user(auth_app, "bob@example.com", "bob")
    client = sign_in(auth_app)

    response = client.patch(
        f"{ACCOUNT}/profile", json={"username": "bob", "current_password": PASSWORD}
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "username_unavailable"
    assert "bob" not in response.text
    assert "alice@example.com" not in response.text


def wait_for_a_lock_waiter(app: FastAPI, timeout: float = 10.0) -> bool:
    """True once another backend of the test database waits on a lock (PostgreSQL's view)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with app.state.database.session() as probe:
            waiting = probe.execute(
                text(
                    "SELECT count(*) FROM pg_stat_activity "
                    "WHERE datname = current_database() AND wait_event_type = 'Lock'"
                )
            ).scalar_one()
        if waiting:
            return True
        time.sleep(0.05)
    return False


def test_two_claims_on_one_username_are_settled_by_the_unique_constraint(
    auth_app: FastAPI,
) -> None:
    """The database constraint, not the duplicate check, decides a concurrent claim.

    Bob's change holds "carol" in an open transaction. Alice's request is started
    while it is open: her duplicate check cannot see the uncommitted name, so it
    passes, and her update then waits on the unique index. Only when PostgreSQL
    reports her request as waiting is Bob's transaction committed. Her request must
    then fail with ``username_unavailable`` and leave her account unchanged.
    """
    alice = make_user(auth_app)
    bob = make_user(auth_app, "bob@example.com", "bob")
    alice_client = sign_in(auth_app)
    outcome: dict[str, Any] = {}

    def alice_claims_carol() -> None:
        outcome["response"] = alice_client.patch(
            f"{ACCOUNT}/profile", json={"username": "carol", "current_password": PASSWORD}
        )

    holder = auth_app.state.database.session_factory()
    try:
        holder.execute(update(User).where(User.id == bob.id).values(username="carol"))
        worker = threading.Thread(target=alice_claims_carol)
        worker.start()
        waited = wait_for_a_lock_waiter(auth_app)
        holder.commit()
    finally:
        if holder.in_transaction():
            holder.rollback()
        holder.close()
    worker.join(timeout=30)

    assert waited, "Alice's change never waited on the unique index"
    assert not worker.is_alive()
    response = outcome["response"]
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "username_unavailable"
    with auth_app.state.database.session() as reader:
        alice_row = reader.get(User, alice.id)
        bob_row = reader.get(User, bob.id)
        assert alice_row is not None
        assert bob_row is not None
        assert alice_row.username == "alice"
        assert bob_row.username == "carol"
        holders = reader.scalars(select(User.id).where(User.username == "carol")).all()
        assert holders == [bob.id]
    # Alice is still signed in and can still use her account.
    assert alice_client.get(f"{ACCOUNT}/profile").json()["username"] == "alice"


def test_keeping_the_same_username_changes_nothing(auth_app: FastAPI) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)

    response = client.patch(
        f"{ACCOUNT}/profile", json={"username": "alice", "current_password": PASSWORD}
    )

    assert response.status_code == 200
    assert response.json()["username"] == "alice"


def test_the_email_address_cannot_be_changed_through_the_profile(auth_app: FastAPI) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)

    response = client.patch(
        f"{ACCOUNT}/profile",
        json={"username": "alice", "current_password": PASSWORD, "email": "x@example.com"},
    )

    assert response.status_code == 422


def test_profile_changes_need_a_csrf_token(auth_app: FastAPI, db: Session) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)
    client.auto_csrf = False

    response = client.patch(
        f"{ACCOUNT}/profile", json={"username": "newname", "current_password": PASSWORD}
    )

    assert response.status_code == 403
    assert user_by_name(db, "alice").username == "alice"


# --- password ---------------------------------------------------------------


def test_a_wrong_current_password_does_not_change_the_password(auth_app: FastAPI) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)

    response = client.post(
        f"{ACCOUNT}/password",
        json={"current_password": "not the password", "new_password": NEW_PASSWORD},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "current_password_incorrect"
    assert client.get(f"{AUTH}/me").status_code == 200
    assert (
        AegisTestClient(auth_app)
        .post(f"{AUTH}/login", json={"email": "alice@example.com", "password": PASSWORD})
        .status_code
        == 200
    )


def test_the_new_password_must_differ_from_the_current_one(auth_app: FastAPI) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)

    response = client.post(
        f"{ACCOUNT}/password", json={"current_password": PASSWORD, "new_password": PASSWORD}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "password_unchanged"


def test_the_password_policy_applies_to_the_new_password(auth_app: FastAPI) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)

    response = client.post(
        f"{ACCOUNT}/password", json={"current_password": PASSWORD, "new_password": "short"}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "password_rejected"


def test_a_password_change_rotates_this_session_and_signs_out_the_others(
    auth_app: FastAPI, db: Session, caplog: pytest.LogCaptureFixture
) -> None:
    make_user(auth_app)
    current = sign_in(auth_app)
    other = sign_in(auth_app)
    old_token = current.session_cookie()
    assert old_token is not None

    with caplog.at_level(logging.INFO):
        response = current.post(
            f"{ACCOUNT}/password",
            json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["csrf_token"]
    assert current.session_cookie() != old_token

    # This browser is still signed in, with its rotated token.
    assert current.get(f"{AUTH}/me").status_code == 200
    # The token the browser held before the change no longer works.
    stale = AegisTestClient(auth_app)
    stale.set_cookie(auth_app.state.auth.settings.session_cookie_name, old_token)
    assert stale.get(f"{AUTH}/me").status_code == 401
    # The other browser is signed out.
    assert other.get(f"{AUTH}/me").status_code == 401

    statuses = {row.revoked_reason for row in session_rows(db, "alice") if row.revoked_at}
    assert statuses == {"password_changed"}
    events = [getattr(record, "event", None) for record in caplog.records]
    assert "auth.password_changed" in events
    assert NEW_PASSWORD not in caplog.text
    assert PASSWORD not in caplog.text


def test_a_password_change_revokes_every_device_and_clears_this_browsers_device_cookie(
    auth_app: FastAPI,
) -> None:
    """D-070: no trusted device outlives the password, and this browser's cookie goes too."""
    user = make_user(auth_app)
    client = sign_in(auth_app)
    sign_in(auth_app)  # a second browser, with its own trusted device
    settings = auth_app.state.auth.settings
    device_token = client.cookies.get(settings.device_cookie_name, domain=COOKIE_DOMAIN)
    old_session_token = client.session_cookie()
    assert device_token is not None
    assert old_session_token is not None
    with auth_app.state.database.session() as reader:
        before = reader.scalars(select(TrustedDevice).where(TrustedDevice.user_id == user.id)).all()
        assert len(before) == 2
        assert all(device.revoked_at is None for device in before)

    response = client.post(
        f"{ACCOUNT}/password", json={"current_password": PASSWORD, "new_password": NEW_PASSWORD}
    )

    assert response.status_code == 200
    # The response clears this browser's device cookie, and the client no longer holds it.
    cleared = [
        header
        for header in response.headers.get_list("set-cookie")
        if header.startswith(f"{settings.device_cookie_name}=")
    ]
    assert len(cleared) == 1
    assert "Max-Age=0" in cleared[0]
    assert client.cookies.get(settings.device_cookie_name, domain=COOKIE_DOMAIN) is None

    # Every device of the account is revoked, and the old device token is no longer trusted.
    with auth_app.state.database.session() as reader:
        after = reader.scalars(select(TrustedDevice).where(TrustedDevice.user_id == user.id)).all()
        assert len(after) == 2
        assert all(device.revoked_reason == "password_changed" for device in after)
        account = reader.get(User, user.id)
        assert account is not None
        assert trusted_devices.find_valid(reader, device_token, account, clock.utcnow()) is None
    assert client.get(f"{AUTH}/devices").json() == []

    # This browser stays signed in with its rotated token; the old token is refused.
    new_session_token = client.session_cookie()
    assert new_session_token is not None
    assert new_session_token != old_session_token
    assert client.get(f"{AUTH}/me").status_code == 200
    stale = AegisTestClient(auth_app)
    stale.set_cookie(settings.session_cookie_name, old_session_token)
    assert stale.get(f"{AUTH}/me").status_code == 401


def test_the_new_password_signs_in_and_the_old_one_does_not(auth_app: FastAPI) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)
    client.post(
        f"{ACCOUNT}/password", json={"current_password": PASSWORD, "new_password": NEW_PASSWORD}
    )

    old = AegisTestClient(auth_app).post(
        f"{AUTH}/login", json={"email": "alice@example.com", "password": PASSWORD}
    )
    new = AegisTestClient(auth_app).post(
        f"{AUTH}/login", json={"email": "alice@example.com", "password": NEW_PASSWORD}
    )

    assert old.status_code == 401
    assert new.status_code == 200


def test_a_password_change_needs_a_csrf_token(auth_app: FastAPI) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)
    client.auto_csrf = False

    response = client.post(
        f"{ACCOUNT}/password", json={"current_password": PASSWORD, "new_password": NEW_PASSWORD}
    )

    assert response.status_code == 403
    assert (
        AegisTestClient(auth_app)
        .post(f"{AUTH}/login", json={"email": "alice@example.com", "password": PASSWORD})
        .status_code
        == 200
    )


def test_password_attempts_are_limited_per_account(auth_app: FastAPI) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)

    for _ in range(5):
        response = client.post(
            f"{ACCOUNT}/password",
            json={"current_password": "wrong one entirely", "new_password": NEW_PASSWORD},
        )
        assert response.status_code == 400

    refused = client.post(
        f"{ACCOUNT}/password", json={"current_password": PASSWORD, "new_password": NEW_PASSWORD}
    )
    assert refused.status_code == 429
    assert int(refused.headers["Retry-After"]) >= 1
    assert refused.json()["error"]["code"] == "too_many_requests"


def test_the_limit_on_changes_is_separate_for_each_account(auth_app: FastAPI) -> None:
    make_user(auth_app)
    make_user(auth_app, "bob@example.com", "bob")
    alice = sign_in(auth_app)
    for _ in range(6):
        alice.patch(
            f"{ACCOUNT}/profile",
            json={"username": "alice", "current_password": "wrong one entirely"},
        )

    bob = sign_in(auth_app, "bob@example.com")
    response = bob.patch(
        f"{ACCOUNT}/profile", json={"username": "bobby", "current_password": PASSWORD}
    )

    assert response.status_code == 200


# --- sessions ---------------------------------------------------------------


def test_the_session_list_contains_only_your_active_sessions(auth_app: FastAPI) -> None:
    make_user(auth_app)
    make_user(auth_app, "bob@example.com", "bob")
    alice = sign_in(auth_app)
    sign_in(auth_app)
    sign_in(auth_app, "bob@example.com")

    response = alice.get(f"{ACCOUNT}/sessions")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    rows = response.json()
    assert len(rows) == 2
    assert sum(1 for row in rows if row["current"]) == 1
    for row in rows:
        assert set(row) == {
            "id",
            "created_at",
            "last_seen_at",
            "expires_at",
            "user_agent",
            "current",
        }
    serialised = response.text
    token = alice.session_cookie()
    assert token is not None
    assert token not in serialised
    assert "token_hash" not in serialised
    assert "ip_address" not in serialised


def test_expired_and_idle_sessions_are_not_listed(auth_app: FastAPI) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)
    expired = sign_in(auth_app)
    idle = sign_in(auth_app)
    expired_hash = hash_token(expired.session_cookie() or "")
    idle_hash = hash_token(idle.session_cookie() or "")
    now = clock.utcnow()
    with auth_app.state.database.session() as writer:
        writer.execute(
            update(UserSession)
            .where(UserSession.token_hash == expired_hash)
            .values(created_at=now - timedelta(hours=2), expires_at=now - timedelta(minutes=1))
        )
        writer.execute(
            update(UserSession)
            .where(UserSession.token_hash == idle_hash)
            .values(last_seen_at=now - timedelta(days=2))
        )
    listed = client.get(f"{ACCOUNT}/sessions").json()

    assert len(listed) == 1
    assert listed[0]["current"] is True


def test_you_can_sign_out_one_of_your_other_sessions(auth_app: FastAPI) -> None:
    make_user(auth_app)
    alice = sign_in(auth_app)
    other = sign_in(auth_app)
    other_id = next(
        row["id"] for row in alice.get(f"{ACCOUNT}/sessions").json() if not row["current"]
    )

    response = alice.delete(f"{ACCOUNT}/sessions/{other_id}")

    assert response.status_code == 204
    assert other.get(f"{AUTH}/me").status_code == 401
    assert alice.get(f"{AUTH}/me").status_code == 200


def test_another_accounts_session_is_reported_as_not_found(auth_app: FastAPI, db: Session) -> None:
    make_user(auth_app)
    make_user(auth_app, "bob@example.com", "bob")
    alice = sign_in(auth_app)
    bob = sign_in(auth_app, "bob@example.com")
    bobs_id = bob.get(f"{ACCOUNT}/sessions").json()[0]["id"]

    response = alice.delete(f"{ACCOUNT}/sessions/{bobs_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "session_not_found"
    assert bob.get(f"{AUTH}/me").status_code == 200


def test_an_unknown_session_identifier_is_not_found(auth_app: FastAPI) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)

    response = client.delete(f"{ACCOUNT}/sessions/00000000-0000-4000-8000-000000000000")

    assert response.status_code == 404


def test_revoking_the_current_session_signs_the_browser_out(auth_app: FastAPI) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)
    current_id = next(
        row["id"] for row in client.get(f"{ACCOUNT}/sessions").json() if row["current"]
    )

    response = client.delete(f"{ACCOUNT}/sessions/{current_id}")

    assert response.status_code == 204
    cleared = response.headers.get_list("set-cookie")
    assert any(
        auth_app.state.auth.settings.session_cookie_name in value and "Max-Age=0" in value
        for value in cleared
    )
    assert client.get(f"{AUTH}/me").status_code == 401


def test_sign_out_other_sessions_keeps_this_one_and_leaves_devices_alone(
    auth_app: FastAPI, db: Session
) -> None:
    make_user(auth_app)
    alice = sign_in(auth_app)
    other = sign_in(auth_app)
    devices_before = alice.get(f"{AUTH}/devices").json()

    response = alice.post(f"{ACCOUNT}/sessions/revoke-others")

    assert response.status_code == 200
    assert response.json() == {"revoked": 1}
    assert response.headers["Cache-Control"] == "no-store"
    assert other.get(f"{AUTH}/me").status_code == 401
    assert alice.get(f"{AUTH}/me").status_code == 200
    assert alice.get(f"{AUTH}/devices").json() == devices_before


def test_session_routes_need_a_session_and_a_csrf_token(auth_app: FastAPI) -> None:
    make_user(auth_app)
    anonymous = AegisTestClient(auth_app)
    assert anonymous.get(f"{ACCOUNT}/sessions").status_code == 401
    assert anonymous.post(f"{ACCOUNT}/sessions/revoke-others").status_code == 401

    client = sign_in(auth_app)
    client.auto_csrf = False
    assert client.post(f"{ACCOUNT}/sessions/revoke-others").status_code == 403


# --- service rules ----------------------------------------------------------


def test_rotating_a_token_replaces_the_stored_hash(auth_app: FastAPI) -> None:
    user = make_user(auth_app)
    now = clock.utcnow()
    with auth_app.state.database.session() as writer:
        target = writer.get(User, user.id)
        assert target is not None
        old_token = sessions.create_session(
            writer, target, auth_app.state.auth.policy, now, client_ip=None, user_agent=None
        )
        row = writer.scalars(select(UserSession).where(UserSession.user_id == user.id)).one()
        old_hash = row.token_hash
        new_token = sessions.rotate_token(writer, row, now)

    with auth_app.state.database.session() as reader:
        stored = reader.scalars(select(UserSession).where(UserSession.user_id == user.id)).one()
        assert stored.token_hash == hash_token(new_token)
        assert stored.token_hash != old_hash
        assert stored.token_hash != hash_token(old_token)


def test_revoking_all_sessions_can_keep_one(auth_app: FastAPI, db: Session) -> None:
    user = make_user(auth_app)
    alice = sign_in(auth_app)
    sign_in(auth_app)
    keep_hash = hash_token(alice.session_cookie() or "")
    keep = db.scalars(select(UserSession).where(UserSession.token_hash == keep_hash)).one()

    with auth_app.state.database.session() as writer:
        count = sessions.revoke_all_sessions(
            writer, user.id, "test", clock.utcnow(), keep_session_id=keep.id
        )
    assert count == 1
    with auth_app.state.database.session() as reader:
        active = [
            row.id
            for row in reader.scalars(select(UserSession).where(UserSession.user_id == user.id))
            if row.revoked_at is None
        ]
    assert active == [keep.id]


def test_a_refused_change_is_logged_without_any_secret(
    auth_app: FastAPI, caplog: pytest.LogCaptureFixture
) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)

    with caplog.at_level(logging.INFO):
        client.patch(
            f"{ACCOUNT}/profile",
            json={"username": "newname", "current_password": "wrong one entirely"},
        )

    events = [getattr(record, "event", None) for record in caplog.records]
    assert "auth.account_change_refused" in events
    assert "wrong one entirely" not in caplog.text
    assert "alice@example.com" not in caplog.text


def test_changing_the_username_does_not_touch_sessions(auth_app: FastAPI, db: Session) -> None:
    make_user(auth_app)
    client = sign_in(auth_app)
    other = sign_in(auth_app)

    response = client.patch(
        f"{ACCOUNT}/profile", json={"username": "renamed", "current_password": PASSWORD}
    )

    assert response.status_code == 200
    assert other.get(f"{AUTH}/me").status_code == 200
    assert all(row.revoked_at is None for row in session_rows(db, "renamed"))
