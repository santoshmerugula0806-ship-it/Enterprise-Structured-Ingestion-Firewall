from pydantic import ValidationError

from .schemas import (
    AIClassification,
    FirewallResponse,
    Intent,
    IngestionResult,
    PriorityParameters,
    RiskLevel,
    TokenMetadata,
)

# Business rules: explicit, deterministic, and NOT left to the model alone.
SLA_BY_PRIORITY = {1: 1, 2: 4, 3: 24, 4: 48, 5: 72}
MIN_CONFIDENCE = 0.5

RISK_PRIORITY_FLOOR = {  # risk level -> most relaxed priority allowed (higher number = less urgent)
    RiskLevel.CRITICAL: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.MEDIUM: 4,
    RiskLevel.LOW: 5,
}


def apply_business_rules(c: AIClassification) -> AIClassification:
    """Override the model where policy requires it."""
    data = c.model_dump()
    # Security incidents are never below high risk.
    if c.intent == Intent.SECURITY_INCIDENT and c.risk_profile in (RiskLevel.LOW, RiskLevel.MEDIUM):
        data["risk_profile"] = RiskLevel.HIGH
    # Priority can't be more relaxed than the risk level allows.
    floor = RISK_PRIORITY_FLOOR[RiskLevel(data["risk_profile"])]
    data["priority"] = min(data["priority"], floor)
    return AIClassification(**data)


def validate_ai_output(raw: dict, tokens: TokenMetadata) -> FirewallResponse:
    """The firewall gate: schema check -> business rules -> accept/reject."""
    try:
        classification = AIClassification.model_validate(raw)
    except ValidationError as exc:
        fields = sorted({".".join(map(str, e["loc"])) or "root" for e in exc.errors()})
        return FirewallResponse(
            accepted=False,
            rejection_reason=f"AI output failed schema validation: {', '.join(fields)}",
            token_metadata=tokens,
        )

    if classification.confidence < MIN_CONFIDENCE:
        return FirewallResponse(
            accepted=False,
            rejection_reason=f"Confidence {classification.confidence:.2f} below threshold {MIN_CONFIDENCE}",
            token_metadata=tokens,
        )

    c = apply_business_rules(classification)
    needs_review = (
        c.risk_profile in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        or c.intent in (Intent.SECURITY_INCIDENT, Intent.TRANSACTION_ISSUE)
    )
    result = IngestionResult(
        intent=c.intent,
        risk_profile=c.risk_profile,
        priority_parameters=PriorityParameters(
            priority=c.priority,
            requires_human_review=needs_review,
            sla_hours=SLA_BY_PRIORITY[c.priority],
        ),
        summary=c.summary,
        confidence=c.confidence,
        token_metadata=tokens,
    )
    return FirewallResponse(accepted=True, result=result, token_metadata=tokens)
