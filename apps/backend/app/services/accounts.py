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


class CurrentPasswordIncorrectError(AppError):
    status_code = HTTPStatus.BAD_REQUEST
    code = "current_password_incorrect"
    message = "The current password is incorrect."


class PasswordUnchangedError(AppError):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    code = "password_unchanged"
    message = "Choose a password that is different from the current one."


class UsernameUnavailableError(AppError):
    status_code = HTTPStatus.CONFLICT
    code = "username_unavailable"
    message = "This username is not available."


def verify_current_password(user: User, password: str, change: str) -> None:
    """Check the password of a signed-in user before a sensitive change (``change`` is logged).

    The failure names no account and no value: the caller is already signed in.
    """
    if not verify_password(user.password_hash, password):
        security_event(
            "auth.account_change_refused",
            "Account change refused: current password incorrect",
            level=logging.WARNING,
            change=change,
            user_id=str(user.id),
        )
        raise CurrentPasswordIncorrectError()


def change_password(
    db: Session, user: User, current_password: str, new_password: str, now: datetime
) -> None:
    """Change the password of a signed-in user (the caller handles sessions and cookies).

    Checks the current password, that the new one differs, and the policy. Every
    trusted device is revoked by ``set_password`` (D-070).
    """
    verify_current_password(user, current_password, "password")
    if verify_password(user.password_hash, new_password):
        raise PasswordUnchangedError()
    set_password(db, user, new_password, now)


def change_username(db: Session, user: User, username: str, current_password: str) -> None:
    """Change the username of a signed-in user after checking the current password.

    ``username`` must already be normalized. A taken name is reported without
    naming the account that holds it.
    """
    verify_current_password(user, current_password, "username")
    if username == user.username:
        return
    if db.scalar(select(User.id).where(User.username == username, User.id != user.id)) is not None:
        raise UsernameUnavailableError()
    user.username = username
    try:
        with db.begin_nested():
            db.flush()
    except IntegrityError as error:
        # A concurrent registration or change took the name after the check above.
        raise UsernameUnavailableError() from error
    security_event("account.username_changed", "Username changed", user_id=str(user.id))


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
