from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Intent(str, Enum):
    TRANSACTION_ISSUE = "transaction_issue"
    SECURITY_INCIDENT = "security_incident"
    ACCOUNT_ACCESS = "account_access"
    GENERAL_INQUIRY = "general_inquiry"
    COMPLAINT = "complaint"
    OTHER = "other"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MessageIn(BaseModel):
    """Incoming request: validated before anything touches the AI."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(..., min_length=3, max_length=2000)

    @field_validator("message")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("message must contain at least 3 non-space characters")
        return v


class PriorityParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    priority: int = Field(..., ge=1, le=5, description="1 = most urgent, 5 = least")
    requires_human_review: bool
    sla_hours: int = Field(..., ge=1, le=168)


class TokenMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_tokens: int = Field(..., ge=0)
    output_tokens: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)


class AIClassification(BaseModel):
    """What the model is asked to return. Strict: unknown fields or values are rejected."""

    model_config = ConfigDict(extra="forbid")

    intent: Intent
    risk_profile: RiskLevel
    priority: int = Field(..., ge=1, le=5)
    summary: str = Field(..., min_length=1, max_length=300)
    confidence: float = Field(..., ge=0.0, le=1.0)


class IngestionResult(BaseModel):
    """Final validated object that is allowed to move downstream."""

    model_config = ConfigDict(extra="forbid")

    intent: Intent
    risk_profile: RiskLevel
    priority_parameters: PriorityParameters
    summary: str
    confidence: float
    token_metadata: TokenMetadata


class FirewallResponse(BaseModel):
    accepted: bool
    result: IngestionResult | None = None
    rejection_reason: str | None = None
    token_metadata: TokenMetadata | None = None
