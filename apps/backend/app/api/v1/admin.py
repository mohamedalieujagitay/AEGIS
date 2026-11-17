"""Instance administration needed by roadmap 2.1 (PRD FR-AUTH-005, FR-AUTH-006).

Only what authentication requires: issuing password reset tokens and turning
open registration on or off. User management is roadmap task 2.2.
"""

from datetime import timedelta
from http import HTTPStatus

from fastapi import APIRouter, Response

from app.api.dependencies import Auth, DbSession, InstanceAdmin
from app.core import clock
from app.core.errors import AppError
from app.core.security_log import security_event
from app.schemas.auth import (
    IssuePasswordResetRequest,
    PasswordResetIssuedResponse,
    RegistrationSetting,
)
from app.schemas.errors import ErrorResponse
from app.services import accounts, password_reset

router = APIRouter(
    prefix="/admin",
    tags=["instance administration"],
    responses={status: {"model": ErrorResponse} for status in (401, 403)},
)


class UserNotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND
    code = "user_not_found"
    message = "No account uses this email address."


@router.post(
    "/password-resets",
    response_model=PasswordResetIssuedResponse,
    status_code=HTTPStatus.CREATED,
    responses={404: {"model": ErrorResponse}},
    summary="Issue a password reset token for a user",
)
def issue_password_reset(
    payload: IssuePasswordResetRequest,
    admin: InstanceAdmin,
    db: DbSession,
    auth: Auth,
    response: Response,
) -> PasswordResetIssuedResponse:
    """The token is returned once. Hand it to the user out of band; no email is sent."""
    user = accounts.find_user_by_email(db, payload.email)
    if user is None:
        raise UserNotFoundError()
    token, expires_at = password_reset.issue_reset_token(
        db,
        user,
        issued_by=admin,
        method="admin",
        ttl=timedelta(minutes=auth.settings.password_reset_token_ttl_minutes),
        now=clock.utcnow(),
    )
    response.headers["Cache-Control"] = "no-store"
    # Commit before responding: the session dependency commits only after the
    # response is returned, so a request that follows this one could read the
    # previous state (found in the browser smoke test, 2026-11-17).
    db.commit()
    return PasswordResetIssuedResponse(
        reset_token=token, reset_path=f"/reset-password#token={token}", expires_at=expires_at
    )


@router.get(
    "/settings/registration", response_model=RegistrationSetting, summary="Open registration"
)
def get_registration(_: InstanceAdmin, db: DbSession) -> RegistrationSetting:
    return RegistrationSetting(enabled=accounts.registration_enabled(db))


@router.put(
    "/settings/registration",
    response_model=RegistrationSetting,
    summary="Turn open registration on or off",
)
def set_registration(
    payload: RegistrationSetting, admin: InstanceAdmin, db: DbSession
) -> RegistrationSetting:
    accounts.set_registration_enabled(db, payload.enabled)
    security_event(
        "admin.registration_changed",
        "Open registration changed",
        actor_id=str(admin.id),
        enabled=payload.enabled,
    )
    # Commit before responding: the session dependency commits only after the
    # response is returned, so a request that follows this one could read the
    # previous state (found in the browser smoke test, 2026-11-17).
    db.commit()
    return RegistrationSetting(enabled=payload.enabled)
