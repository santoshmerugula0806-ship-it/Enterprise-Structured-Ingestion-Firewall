# Enterprise Structured Ingestion Firewall

Receives a support/financial message, classifies it with an LLM (Groq API),
converts it to structured JSON, validates it with Pydantic + business rules,
and accepts or rejects it before it can go downstream.

Stack: Python, FastAPI, Pydantic, Groq (OpenAI-compatible API), plain HTML/CSS/JS, Pytest.

## Setup (Windows PowerShell)

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env      # then open .env and paste your real GROQ_API_KEY
```

## Run

```powershell
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 (the frontend is served by the backend).
API docs: http://127.0.0.1:8000/docs

## Test

```powershell
python -m pytest -q
```

## Structure

```
backend/app/schemas.py     Pydantic models (input, AI output, final result)
backend/app/ai_service.py  Groq call + token usage
backend/app/firewall.py    Output validation + business rules (risk, priority, review)
backend/app/main.py        FastAPI endpoints, serves the frontend
backend/tests/             Pytest tests
frontend/                  index.html, style.css, script.js
```

Never commit `.env` or share your API key.
