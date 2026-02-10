# pm-decision-copilot

A lightweight product decision journaling API built with FastAPI and SQLite.

## Setup

```bash
pip install fastapi uvicorn sqlalchemy pydantic requests jinja2
```

## Run the API

```bash
uvicorn main:app --reload
```

Then open the forwarded port in Codespaces to view the UI at `/`.
If you're running locally, open `http://127.0.0.1:8000/`.

## Sample data

Start the API, then run:

```bash
python sample_data.py
```
