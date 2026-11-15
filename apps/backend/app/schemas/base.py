"""Base classes for API schemas."""

from pydantic import BaseModel, ConfigDict


class RequestModel(BaseModel):
    """Base class for every request body.

    Unknown fields are rejected instead of silently ignored, so typos and
    unexpected input are reported to the client. Surrounding whitespace is
    stripped from strings.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)
