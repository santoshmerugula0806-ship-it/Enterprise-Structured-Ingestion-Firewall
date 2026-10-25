from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .ai_service import AIServiceError, classify_message
from .firewall import validate_ai_output
from .schemas import FirewallResponse, MessageIn

app = FastAPI(title="Enterprise Structured Ingestion Firewall")

# Only needed if index.html is opened straight from disk (file://) or hosted elsewhere.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["null", "http://localhost:5500", "http://127.0.0.1:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ingest", response_model=FirewallResponse)
def ingest(payload: MessageIn) -> FirewallResponse:
    """Input validation (Pydantic) -> AI classification -> output validation -> accept/reject."""
    try:
        raw, tokens = classify_message(payload.message)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return validate_ai_output(raw, tokens)


# Serve the plain HTML/CSS/JS frontend at "/" (mounted last so API routes win).
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
