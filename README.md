# premortem-action-copilot

A FastAPI web app that helps product managers convert premortem concerns into 1-2 near-term mitigation actions for a two-week horizon.

## What V0 includes

- Structured concern intake with free text context.
- Severity and impact inputs.
- 1-2 generated actions with metadata:
  - owner role
  - due-in-days
  - impact / effort / confidence score
  - leading indicator
- Multi-user persistence by name/email.
- 60-day retention for premortem concerns and generated actions.
- LLM-first generation when `OPENAI_API_KEY` is available, with deterministic fallback.

## Setup

```bash
pip install fastapi uvicorn sqlalchemy pydantic email-validator requests jinja2
```

## Run locally

```bash
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/`.

## Optional OpenAI configuration

```bash
export OPENAI_API_KEY=your_key_here
export OPENAI_MODEL=gpt-4o-mini
```

Without an API key, the app uses deterministic generation.

## Deploy to Render

1. Create a new **Web Service** from this repo.
2. Set build command:

```bash
pip install fastapi uvicorn sqlalchemy pydantic email-validator requests jinja2
```

3. Set start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

4. Add environment variables:
   - `OPENAI_API_KEY` (optional but recommended)
   - `OPENAI_MODEL` (optional)
