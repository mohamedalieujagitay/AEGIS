"""Trusted-device management over HTTP (DECISIONS.md D-070).

Each test runs the real application on a migrated database. The attack
scenario (failures from many addresses) makes the account-wide delay active,
so the tests can tell whether a browser still holds its exemption.
"""

from collections.abc import Callable
from http.cookies import SimpleCookie

import pytest
from fastapi import FastAPI
from helpers import AegisTestClient, FakeClock
from httpx2 import Response
from sqlalchemy import select

from app.models.trusted_device import TrustedDevice
from app.services import accounts

PASSWORD = "correct horse battery staple"
NEW_PASSWORD = "a completely different passphrase"
AUTH = "/api/v1/auth"
DEVICE = "__Host-aegis_device"
ALICE = {"email": "alice@example.com", "password": PASSWORD}


@pytest.fixture
def app(make_auth_app: Callable[..., FastAPI]) -> FastAPI:
    application = make_auth_app()
    with application.state.database.session() as db:
        accounts.create_account(db, email="alice@example.com", username="alice", password=PASSWORD)
    return application


def add_account(app: FastAPI, email: str, username: str) -> None:
    with app.state.database.session() as db:
        accounts.create_account(db, email=email, username=username, password=PASSWORD)


def device_cookie_of(client: AegisTestClient) -> str:
    return client.cookies.get(DEVICE, domain="testserver.local") or ""


def sign_in(
    app: FastAPI, address: str, email: str = "alice@example.com", password: str = PASSWORD
) -> AegisTestClient:
    client = AegisTestClient(app, client=(address, 50000))
    response = client.post(f"{AUTH}/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return client


def attack(app: FastAPI, *, email: str = "alice@example.com", count: int = 21) -> None:
    """Failures from distinct addresses: the account-wide delay is in force for ``email``."""
    for index in range(count):
        AegisTestClient(app, client=(f"203.0.113.{index}", 50000)).post(
            f"{AUTH}/login", json={"email": email, "password": "wrong password!"}
        )


def exempt_status(app: FastAPI, cookie: str, *, address: str = "198.51.100.7") -> int:
    """Status of a sign-in during the attack, presenting ``cookie`` as the device cookie."""
    client = AegisTestClient(app, client=(address, 50100))
    client.set_cookie(DEVICE, cookie)
    return client.post(
        f"{AUTH}/login", json={"email": "alice@example.com", "password": PASSWORD}
    ).status_code


def set_cookies(response: Response) -> dict[str, SimpleCookie]:
    cookies = {}
    for header in response.headers.get_list("set-cookie"):
        cookie: SimpleCookie = SimpleCookie()
        cookie.load(header)
        [name] = cookie.keys()
        cookies[name] = cookie
    return cookies


def test_listing_marks_the_current_browser_and_shows_no_token(app: FastAPI) -> None:
    client = sign_in(app, "198.51.100.7")
    response = client.get(f"{AUTH}/devices")
    assert response.status_code == 200
    [device] = response.json()
    assert device["current"] is True
    assert set(device) == {
        "id",
        "created_at",
        "expires_at",
        "last_used_at",
        "user_agent",
        "current",
    }
    assert device_cookie_of(client) not in response.text
    assert response.headers["cache-control"] == "no-store"


def test_device_management_requires_a_session(app: FastAPI) -> None:
    anonymous = AegisTestClient(app)
    assert anonymous.get(f"{AUTH}/devices").status_code == 401
    assert (
        anonymous.delete(f"{AUTH}/devices/00000000-0000-4000-8000-000000000001").status_code == 401
    )


def test_revoking_a_device_requires_csrf(app: FastAPI) -> None:
    client = sign_in(app, "198.51.100.7")
    [device] = client.get(f"{AUTH}/devices").json()
    unprotected = AegisTestClient(app, auto_csrf=False)
    unprotected.set_cookie(
        app.state.auth.settings.session_cookie_name, client.session_cookie() or ""
    )
    response = unprotected.delete(f"{AUTH}/devices/{device['id']}")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_failed"


def test_a_user_cannot_see_or_revoke_another_accounts_device(app: FastAPI) -> None:
    add_account(app, "bob@example.com", "bob")
    alice = sign_in(app, "198.51.100.7")
    [device] = alice.get(f"{AUTH}/devices").json()
    bob = sign_in(app, "198.51.100.9", email="bob@example.com")
    assert all(item["id"] != device["id"] for item in bob.get(f"{AUTH}/devices").json())
    response = bob.delete(f"{AUTH}/devices/{device['id']}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "device_not_found"
    assert [item["id"] for item in alice.get(f"{AUTH}/devices").json()] == [device["id"]]


def test_revoking_a_device_removes_its_exemption(app: FastAPI) -> None:
    client = sign_in(app, "198.51.100.7")
    cookie = device_cookie_of(client)
    [device] = client.get(f"{AUTH}/devices").json()
    response = client.delete(f"{AUTH}/devices/{device['id']}")
    assert response.status_code == 204
    assert set_cookies(response)[DEVICE][DEVICE]["max-age"] == "0"
    attack(app)
    assert exempt_status(app, cookie) == 429


def test_an_expired_device_gets_no_exemption(app: FastAPI, clock: FakeClock) -> None:
    cookie = device_cookie_of(sign_in(app, "198.51.100.7"))
    clock.advance(days=30, seconds=1)
    attack(app)
    assert exempt_status(app, cookie) == 429


def test_a_device_cookie_copied_to_another_account_gets_no_exemption(app: FastAPI) -> None:
    add_account(app, "bob@example.com", "bob")
    stolen = device_cookie_of(sign_in(app, "198.51.100.7"))
    attack(app, email="bob@example.com")  # the delay must be active for bob's account
    bob = AegisTestClient(app, client=("198.51.100.9", 50100))
    bob.set_cookie(DEVICE, stolen)
    response = bob.post(f"{AUTH}/login", json={"email": "bob@example.com", "password": PASSWORD})
    assert response.status_code == 429


def test_ordinary_sign_out_keeps_the_device(app: FastAPI) -> None:
    client = sign_in(app, "198.51.100.7")
    cookie = device_cookie_of(client)
    assert client.post(f"{AUTH}/logout").status_code == 204
    attack(app)
    assert exempt_status(app, cookie) == 200


def test_a_password_reset_revokes_the_devices(app: FastAPI) -> None:
    client = sign_in(app, "198.51.100.7")
    cookie = device_cookie_of(client)
    admin_email = "admin@example.com"
    add_account(app, admin_email, "admin")
    with app.state.database.session() as db:
        admin = accounts.find_user_by_email(db, admin_email)
        assert admin is not None
        admin.is_instance_admin = True
    admin_client = sign_in(app, "198.51.100.8", email=admin_email)
    issued = admin_client.post("/api/v1/admin/password-resets", json={"email": "alice@example.com"})
    assert issued.status_code == 201, issued.text
    token = issued.json()["reset_token"]
    reset = AegisTestClient(app).post(
        f"{AUTH}/password/reset", json={"token": token, "new_password": NEW_PASSWORD}
    )
    assert reset.status_code == 204
    with app.state.database.session() as db:
        alice = accounts.find_user_by_email(db, "alice@example.com")
        assert alice is not None
        devices = db.scalars(select(TrustedDevice).where(TrustedDevice.user_id == alice.id)).all()
        assert devices
        assert all(device.revoked_reason == "password_changed" for device in devices)
    attack(app)
    assert exempt_status(app, cookie) == 429
