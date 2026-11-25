
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class IncidentReport(BaseModel):

    pod_name: str

    namespace: str

    severity: Literal[
        "critical",
        "high",
        "medium",
        "low",
        "unknown"
    ]

    root_cause: str

    evidence: list[str] = Field(
        description="Evidence from Kubernetes status, logs, and events"
    )

    recommended_actions: list[str] = Field(
        description="Recommended investigation or remediation steps"
    )

    missing_information: list[str] = Field(
        description="Additional information required to confirm the diagnosis"
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the diagnosis, from 0 to 1"
    )

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_percentage_confidence(cls, value: object) -> object:
        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and 1 < value <= 100
        ):
            return value / 100

        return value

    requires_human_approval: bool = Field(
        description="Whether approval is required before taking action"
    )
