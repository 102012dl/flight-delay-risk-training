"""Typed HTTP boundary for the existing flight-delay risk classifier."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt

from .classifier import classify_delay_risk


class RiskRequest(BaseModel):
    """The explicit, strict request contract for one classification."""

    model_config = ConfigDict(extra="forbid")

    delay_minutes: StrictInt = Field(ge=0)
    weather_risk: StrictBool
    crew_issue: StrictBool


class RiskResponse(BaseModel):
    """Minimal public response; classifier internals remain private."""

    risk_category: Literal["LOW", "MEDIUM", "HIGH"]


app = FastAPI(
    title="Flight Delay Risk API",
    description="A training API boundary around a deterministic risk classifier.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Return deterministic service health without external dependencies."""
    return {"status": "ok"}


@app.post("/risk", response_model=RiskResponse)
def risk(request: RiskRequest) -> RiskResponse:
    """Delegate the validated request to the existing domain classifier."""
    category = classify_delay_risk(
        request.delay_minutes,
        request.weather_risk,
        request.crew_issue,
    )
    return RiskResponse(risk_category=category)
