"""Trusted devices (DECISIONS.md D-070), against the real database.

Covers the remediation conditions: only hashes are stored, a device belongs to
one account, lifetime is at most 30 days, password changes and deactivation
revoke every device, devices can be revoked individually, and a device never
authenticates a user.
"""

import hashlib
import logging
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from sqlalchemy import select, text

from app.core.security import hash_token
from app.models.trusted_device import TrustedDevice
from app.models.user import User
from app.services import accounts, trusted_devices

PASSWORD = "correct horse battery staple"
NOW = datetime(2026, 11, 17, 9, 0, tzinfo=UTC)
ONE_DAY = timedelta(days=1)


def make_account(app: FastAPI, email: str, username: str) -> User:
    with app.state.database.session() as db:
        return accounts.create_account(db, email=email, username=username, password=PASSWORD)


def issue_for(app: FastAPI, user_id: uuid.UUID, now: datetime = NOW, days: int = 30) -> str:
    with app.state.database.session() as db:
        user = db.get(User, user_id)
        assert user is not None
        return trusted_devices.issue(
            db, user, now=now, lifetime=timedelta(days=days), user_agent="pytest-browser"
        )


def valid_for(app: FastAPI, token: str | None, user_id: uuid.UUID, now: datetime = NOW) -> bool:
    with app.state.database.session() as db:
        user = db.get(User, user_id)
        assert user is not None
        return trusted_devices.find_valid(db, token, user, now) is not None


def test_only_the_hash_of_a_device_token_is_stored(auth_app: FastAPI) -> None:
    user = make_account(auth_app, "alice@example.com", "alice")
    token = issue_for(auth_app, user.id)
    with auth_app.state.database.session() as db:
        [row] = db.scalars(select(TrustedDevice)).all()
        assert row.token_hash == hashlib.sha256(token.encode()).hexdigest()
        assert row.token_hash == hash_token(token)
        dump = db.execute(text("SELECT trusted_devices::text FROM trusted_devices")).scalars().all()
    assert all(token not in value for value in dump)


def test_a_device_is_valid_for_its_own_account_only(
    auth_app: FastAPI, caplog: pytest.LogCaptureFixture
) -> None:
    alice = make_account(auth_app, "alice@example.com", "alice")
    bob = make_account(auth_app, "bob@example.com", "bob")
    token = issue_for(auth_app, alice.id)
    assert valid_for(auth_app, token, alice.id)
    with caplog.at_level(logging.WARNING, logger="app.security"):
        assert not valid_for(auth_app, token, bob.id)
    assert any(getattr(r, "event", None) == "auth.device_rejected" for r in caplog.records)
    assert token not in caplog.text


def test_missing_or_unknown_tokens_are_not_valid(auth_app: FastAPI) -> None:
    user = make_account(auth_app, "alice@example.com", "alice")
    issue_for(auth_app, user.id)
    assert not valid_for(auth_app, None, user.id)
    assert not valid_for(auth_app, "", user.id)
    assert not valid_for(auth_app, "not-a-device-token", user.id)


def test_devices_last_thirty_days_and_no_longer(auth_app: FastAPI) -> None:
    user = make_account(auth_app, "alice@example.com", "alice")
    token = issue_for(auth_app, user.id, days=30)
    assert valid_for(auth_app, token, user.id, NOW + timedelta(days=30) - timedelta(seconds=1))
    assert not valid_for(auth_app, token, user.id, NOW + timedelta(days=30))


def test_lifetime_above_thirty_days_is_refused(auth_app: FastAPI) -> None:
    user = make_account(auth_app, "alice@example.com", "alice")
    with pytest.raises(ValueError, match="30 days"):
        issue_for(auth_app, user.id, days=31)


def test_use_does_not_extend_the_lifetime(auth_app: FastAPI) -> None:
    user = make_account(auth_app, "alice@example.com", "alice")
    token = issue_for(auth_app, user.id)
    with auth_app.state.database.session() as db:
        device = db.scalars(select(TrustedDevice)).one()
        trusted_devices.mark_used(device, NOW + ONE_DAY)
        assert device.expires_at == NOW + timedelta(days=30)
    assert not valid_for(auth_app, token, user.id, NOW + timedelta(days=30))


def test_a_device_can_be_revoked_individually(auth_app: FastAPI) -> None:
    user = make_account(auth_app, "alice@example.com", "alice")
    first = issue_for(auth_app, user.id)
    second = issue_for(auth_app, user.id)
    with auth_app.state.database.session() as db:
        devices = db.scalars(select(TrustedDevice).order_by(TrustedDevice.created_at)).all()
        target = devices[0]
        assert trusted_devices.revoke(db, user.id, target.id, "revoked_by_user", NOW)
    assert not valid_for(auth_app, first, user.id)
    assert valid_for(auth_app, second, user.id)


def test_another_accounts_device_cannot_be_revoked(auth_app: FastAPI) -> None:
    alice = make_account(auth_app, "alice@example.com", "alice")
    bob = make_account(auth_app, "bob@example.com", "bob")
    token = issue_for(auth_app, alice.id)
    with auth_app.state.database.session() as db:
        device = db.scalars(select(TrustedDevice)).one()
        assert not trusted_devices.revoke(db, bob.id, device.id, "revoked_by_user", NOW)
    assert valid_for(auth_app, token, alice.id)


def test_a_revoked_device_is_not_listed_or_valid(auth_app: FastAPI) -> None:
    user = make_account(auth_app, "alice@example.com", "alice")
    token = issue_for(auth_app, user.id)
    with auth_app.state.database.session() as db:
        device = db.scalars(select(TrustedDevice)).one()
        trusted_devices.revoke(db, user.id, device.id, "revoked_by_user", NOW)
        assert trusted_devices.list_for_user(db, user.id, NOW) == []
    assert not valid_for(auth_app, token, user.id)


def test_a_password_reset_revokes_every_device(auth_app: FastAPI) -> None:
    user = make_account(auth_app, "alice@example.com", "alice")
    tokens = [issue_for(auth_app, user.id) for _ in range(3)]
    with auth_app.state.database.session() as db:
        db_user = db.get(User, user.id)
        assert db_user is not None
        accounts.set_password(db, db_user, "a completely different passphrase", NOW + ONE_DAY)
    for token in tokens:
        assert not valid_for(auth_app, token, user.id, NOW + ONE_DAY)


def test_deactivation_ends_sessions_and_devices_and_blocks_trust(auth_app: FastAPI) -> None:
    user = make_account(auth_app, "alice@example.com", "alice")
    token = issue_for(auth_app, user.id)
    with auth_app.state.database.session() as db:
        db_user = db.get(User, user.id)
        assert db_user is not None
        accounts.deactivate(db, db_user, NOW)
    assert not valid_for(auth_app, token, user.id)
    with auth_app.state.database.session() as db:
        remaining = db.scalars(select(TrustedDevice)).all()
        assert remaining
        assert all(device.revoked_reason == "deactivated" for device in remaining)


def test_ended_devices_are_purged_after_the_retention_period(auth_app: FastAPI) -> None:
    user = make_account(auth_app, "alice@example.com", "alice")
    issue_for(auth_app, user.id, now=NOW - timedelta(days=60), days=30)  # expired a month ago
    issue_for(auth_app, user.id, now=NOW)  # still valid
    with auth_app.state.database.session() as db:
        assert trusted_devices.purge_ended(db, NOW) == 1
        assert len(db.scalars(select(TrustedDevice)).all()) == 1


def test_a_device_never_authenticates(auth_app: FastAPI) -> None:
    from helpers import AegisTestClient

    user = make_account(auth_app, "alice@example.com", "alice")
    token = issue_for(auth_app, user.id)
    client = AegisTestClient(auth_app)
    client.set_cookie(auth_app.state.auth.settings.device_cookie_name, token)
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
