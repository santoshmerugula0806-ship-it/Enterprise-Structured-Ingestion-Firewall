import pytest
from pydantic import ValidationError

from app.firewall import validate_ai_output
from app.schemas import AIClassification, MessageIn, TokenMetadata

TOKENS = TokenMetadata(input_tokens=100, output_tokens=30, total_tokens=130)


def good(**over):
    base = {
        "intent": "transaction_issue",
        "risk_profile": "medium",
        "priority": 3,
        "summary": "Bank transfer failed.",
        "confidence": 0.9,
    }
    base.update(over)
    return base


def test_message_rejects_empty_and_blank():
    with pytest.raises(ValidationError):
        MessageIn(message="")
    with pytest.raises(ValidationError):
        MessageIn(message="    ")


def test_message_rejects_too_long_and_extra_fields():
    with pytest.raises(ValidationError):
        MessageIn(message="x" * 2001)
    with pytest.raises(ValidationError):
        MessageIn(message="hello there", role="admin")


def test_valid_output_accepted():
    r = validate_ai_output(good(), TOKENS)
    assert r.accepted and r.result.intent.value == "transaction_issue"
    assert r.result.token_metadata.total_tokens == 130


def test_invalid_intent_rejected():
    r = validate_ai_output(good(intent="wire_money_now"), TOKENS)
    assert not r.accepted and "intent" in r.rejection_reason


def test_missing_field_rejected():
    raw = good()
    del raw["risk_profile"]
    assert not validate_ai_output(raw, TOKENS).accepted


def test_out_of_range_priority_and_extra_field_rejected():
    assert not validate_ai_output(good(priority=9), TOKENS).accepted
    assert not validate_ai_output(good(approve_refund=True), TOKENS).accepted


def test_low_confidence_rejected():
    r = validate_ai_output(good(confidence=0.2), TOKENS)
    assert not r.accepted and "Confidence" in r.rejection_reason


def test_security_incident_forced_to_high_risk_and_urgent():
    r = validate_ai_output(
        good(intent="security_incident", risk_profile="low", priority=5), TOKENS
    )
    assert r.accepted
    assert r.result.risk_profile.value == "high"
    assert r.result.priority_parameters.priority <= 2
    assert r.result.priority_parameters.requires_human_review


def test_classification_schema_strict():
    with pytest.raises(ValidationError):
        AIClassification(**good(confidence=1.5))
