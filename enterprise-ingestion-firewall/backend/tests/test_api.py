from fastapi.testclient import TestClient

from app import main
from app.ai_service import AIServiceError
from app.schemas import TokenMetadata

client = TestClient(main.app)
TOKENS = TokenMetadata(input_tokens=50, output_tokens=20, total_tokens=70)
GOOD = {
    "intent": "account_access",
    "risk_profile": "low",
    "priority": 4,
    "summary": "User wants to reset password.",
    "confidence": 0.95,
}


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_ingest_accepts_valid(monkeypatch):
    monkeypatch.setattr(main, "classify_message", lambda m: (GOOD, TOKENS))
    r = client.post("/ingest", json={"message": "I want to reset my password."})
    assert r.status_code == 200
    body = r.json()
    assert body["accepted"] is True
    assert body["result"]["token_metadata"]["input_tokens"] == 50


def test_ingest_rejects_malformed_ai_output(monkeypatch):
    monkeypatch.setattr(main, "classify_message", lambda m: ({"intent": "hack"}, TOKENS))
    r = client.post("/ingest", json={"message": "hello there"})
    assert r.status_code == 200
    assert r.json()["accepted"] is False


def test_ingest_invalid_request_422():
    assert client.post("/ingest", json={"message": ""}).status_code == 422
    assert client.post("/ingest", json={}).status_code == 422


def test_ingest_provider_failure_502(monkeypatch):
    def boom(m):
        raise AIServiceError("AI provider call failed: Timeout")

    monkeypatch.setattr(main, "classify_message", boom)
    assert client.post("/ingest", json={"message": "hello there"}).status_code == 502


def test_frontend_served_at_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "Ingestion Firewall" in r.text
    assert client.get("/script.js").status_code == 200
