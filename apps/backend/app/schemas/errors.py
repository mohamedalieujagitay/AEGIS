"""Error response schema shared by every endpoint."""

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """One problem with the request, typically a validation error."""

    location: list[str | int] = Field(
        description="Where the problem is, for example ['body', 'name'] or ['query', 'page'].",
    )
    message: str = Field(description="Human-readable description of the problem.")
    type: str = Field(description="Machine-readable problem type, for example 'missing'.")


class ErrorBody(BaseModel):
    code: str = Field(description="Stable machine-readable error code, for example 'not_found'.")
    message: str = Field(description="Human-readable summary. Never contains internal details.")
    request_id: str | None = Field(
        default=None, description="ID of the request, also returned in the X-Request-ID header."
    )
    details: list[ErrorDetail] | None = Field(
        default=None, description="Individual problems, for validation errors."
    )


class ErrorResponse(BaseModel):
    """Body of every error response."""

    error: ErrorBody
