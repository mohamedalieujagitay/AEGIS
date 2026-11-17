"""Accounts: registration, sign-in and passwords (PRD FR-AUTH-001, -002, -006).

Sign-in never reveals whether an account exists: an unknown email address,
a wrong password and an inactive account all produce the same error, after
the same amount of password-hashing work.
"""

import logging
import uuid
from datetime import datetime
from http import HTTPStatus

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.identity import password_problems
from app.core.security import (
    burn_password_check,
    hash_password,
    password_needs_rehash,
    verify_password,
)
from app.core.security_log import security_event
from app.models.instance_settings import InstanceSettings
from app.models.user import User
from app.services import sessions, trusted_devices


class InvalidCredentialsError(AppError):
    status_code = HTTPStatus.UNAUTHORIZED
    code = "invalid_credentials"
    message = "The email address or password is incorrect."


class RegistrationDisabledError(AppError):
    status_code = HTTPStatus.FORBIDDEN
    code = "registration_disabled"
    message = "Registration is disabled. Ask your instance administrator for an account."


class RegistrationRejectedError(AppError):
    status_code = HTTPStatus.CONFLICT
    code = "registration_rejected"
    message = "These details cannot be used to create an account."


class PasswordRejectedError(AppError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    code = "password_rejected"
    message = "The password does not meet the requirements."

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__(" ".join(problems))


def check_password(password: str, *, email: str, username: str) -> None:
    problems = password_problems(password, email=email, username=username)
    if problems:
        raise PasswordRejectedError(problems)


def registration_enabled(db: Session) -> bool:
    settings = db.get(InstanceSettings, 1)
    return bool(settings and settings.registration_enabled)


def set_registration_enabled(db: Session, enabled: bool) -> None:
    settings = db.get(InstanceSettings, 1)
    if settings is None:
        db.add(InstanceSettings(id=1, registration_enabled=enabled))
    else:
        settings.registration_enabled = enabled
    db.flush()


def create_account(
    db: Session,
    *,
    email: str,
    username: str,
    password: str,
    instance_admin: bool = False,
) -> User:
    """Create an account. ``email`` and ``username`` must already be normalized.

    Raises ``PasswordRejectedError`` or, if the email address or username is
    taken, ``RegistrationRejectedError`` (which does not say which one).
    """
    check_password(password, email=email, username=username)
    user = User(
        id=uuid.uuid4(),
        email=email,
        username=username,
        password_hash=hash_password(password),
        is_instance_admin=instance_admin,
    )
    try:
        with db.begin_nested():
            db.add(user)
            db.flush()
    except IntegrityError as error:
        raise RegistrationRejectedError() from error
    return user


def authenticate(db: Session, email: str, password: str, now: datetime) -> User:
    """Return the user for valid credentials, or raise ``InvalidCredentialsError``.

    Upgrades the stored hash if it uses older Argon2 parameters.
    """
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        burn_password_check(password)
        security_event(
            "auth.login_failed",
            "Sign-in failed",
            level=logging.WARNING,
            reason="invalid_credentials",
            account_known=False,
        )
        raise InvalidCredentialsError()
    if not verify_password(user.password_hash, password) or not user.is_active:
        security_event(
            "auth.login_failed",
            "Sign-in failed",
            level=logging.WARNING,
            reason="invalid_credentials" if user.is_active else "inactive_account",
            user_id=str(user.id),
        )
        raise InvalidCredentialsError()
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
        security_event("auth.password_rehashed", "Password hash upgraded", user_id=str(user.id))
    user.last_login_at = now
    return user


def set_password(db: Session, user: User, new_password: str, now: datetime) -> None:
    """Replace the password after checking the policy.

    Every trusted device of the account is revoked as well (D-070): a device
    must not outlive the password it was trusted with. Callers revoke sessions.
    """
    check_password(new_password, email=user.email, username=user.username)
    user.password_hash = hash_password(new_password)
    user.password_changed_at = now
    trusted_devices.revoke_all(db, user.id, "password_changed", now)
    db.flush()


def deactivate(db: Session, user: User, now: datetime) -> None:
    """Deactivate an account: it cannot sign in, and its sessions and devices end at once (D-070).

    No endpoint calls this in v0.1.0; account management is roadmap task 2.2.
    """
    user.is_active = False
    sessions.revoke_all_sessions(db, user.id, "deactivated", now)
    trusted_devices.revoke_all(db, user.id, "deactivated", now)
    security_event("auth.account_deactivated", "Account deactivated", user_id=str(user.id))
    db.flush()


def find_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()
