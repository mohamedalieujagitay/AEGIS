"""Authentication request and response schemas.

Password fields are taken exactly as typed: unlike other strings, surrounding
whitespace is not stripped, because it is part of the password.
"""

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator

from app.core.identity import (
    PASSWORD_MAX_LENGTH,
    normalize_email,
    normalize_email_for_lookup,
    normalize_username,
)
from app.schemas.base import RequestModel

Password = Annotated[
    str, StringConstraints(strip_whitespace=False, min_length=1, max_length=PASSWORD_MAX_LENGTH)
]
"""A password as typed. The full policy is checked by the accounts service."""

LoginPassword = Annotated[
    str, StringConstraints(strip_whitespace=False, min_length=1, max_length=256)
]
Token = Annotated[
    str, StringConstraints(min_length=16, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
]


class RegisterRequest(RequestModel):
    email: str = Field(max_length=320, description="Email address; stored in lower case.")
    username: str = Field(max_length=64, description="3 to 32 letters, digits, '.', '-' or '_'.")
    password: Password

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("username")
    @classmethod
    def _username(cls, value: str) -> str:
        return normalize_username(value)


class LoginRequest(RequestModel):
    email: str = Field(max_length=320)
    password: LoginPassword

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        # Same normalization as registration (D-071). Not rejected when invalid:
        # such an address simply fails to sign in, with the generic error.
        return normalize_email_for_lookup(value)


class PasswordResetRequest(RequestModel):
    token: Token
    new_password: Password


class IssuePasswordResetRequest(RequestModel):
    email: str = Field(max_length=320)

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return normalize_email(value)


class RegistrationSetting(RequestModel):
    enabled: bool


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    is_instance_admin: bool


class CsrfResponse(BaseModel):
    csrf_token: str = Field(
        description="Send in the X-CSRF-Token header of state-changing requests."
    )


class SessionResponse(BaseModel):
    user: UserResponse
    csrf_token: str = Field(description="New CSRF token, bound to the new session.")


class AuthOptionsResponse(BaseModel):
    registration_enabled: bool
    session_idle_timeout_minutes: int
    session_absolute_timeout_hours: int


class PasswordResetIssuedResponse(BaseModel):
    reset_token: str = Field(description="Shown once. Hand it to the user out of band.")
    reset_path: str = Field(description="Path of the reset page, with the token in the fragment.")
    expires_at: datetime


class TrustedDeviceResponse(BaseModel):
    """A browser trusted for sign-in. The token and its hash are never returned (D-070)."""

    id: uuid.UUID
    created_at: datetime
    expires_at: datetime
    last_used_at: datetime | None
    user_agent: str | None
    current: bool = Field(description="True for the browser making this request.")
