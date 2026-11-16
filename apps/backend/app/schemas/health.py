"""Health check response schemas."""

from typing import Literal

from pydantic import BaseModel, Field

CheckStatus = Literal["ok", "unavailable"]


class LivenessResponse(BaseModel):
    status: Literal["ok"] = Field(description="The API process is running and serving requests.")


class ReadinessChecks(BaseModel):
    database: CheckStatus = Field(description="PostgreSQL connectivity.")
    broker: CheckStatus = Field(description="Valkey (message broker) connectivity.")


class ReadinessResponse(BaseModel):
    status: Literal["ready"] = Field(
        description="Every dependency needed to serve requests is available."
    )
    checks: ReadinessChecks
