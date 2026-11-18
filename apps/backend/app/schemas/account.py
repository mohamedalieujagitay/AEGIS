"""Account management schemas: profile, password and sessions (roadmap task 2.2).

Session responses never carry a token, a token hash or an IP address.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.identity import normalize_username
from app.schemas.auth import Password
from app.schemas.base import RequestModel


class ProfileResponse(BaseModel):
    email: str = Field(description="The sign-in address. Read-only (no email change in v0.1.0).")
    username: str
    created_at: datetime
    is_active: bool = Field(description="Whether the account can sign in.")


class UpdateProfileRequest(RequestModel):
    username: str = Field(max_length=64, description="The new username.")
    current_password: Password = Field(description="Required to change the username.")

    @field_validator("username")
    @classmethod
    def _username(cls, value: str) -> str:
        return normalize_username(value)


class ChangePasswordRequest(RequestModel):
    current_password: Password
    new_password: Password


class PasswordChangedResponse(BaseModel):
    csrf_token: str = Field(
        description="A new CSRF token, bound to the rotated session. Replaces the previous one."
    )


class ActiveSessionResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime = Field(description="When the session ends, whatever its activity.")
    user_agent: str | None = Field(description="The browser that signed in, as it reported itself.")
    current: bool = Field(description="True for the session of this request.")


class RevokedSessionsResponse(BaseModel):
    revoked: int = Field(description="Number of other sessions that were signed out.")
