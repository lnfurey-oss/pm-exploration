from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Generator, List

import requests
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from models import (
    Assumption,
    AssumptionCreate,
    AssumptionRead,
    Base,
    Constraint,
    Decision,
    DecisionCreate,
    DecisionRead,
    MitigationAction,
    Outcome,
    OutcomeCreate,
    PremortemConcern,
    PremortemConcernCreate,
    PremortemPlanRead,
    User,
)

DATABASE_URL = "sqlite:///./decisions.db"
RETENTION_DAYS = 60

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Premortem Decision Copilot")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def cleanup_expired_concerns(db: Session) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    expired = db.scalars(
        select(PremortemConcern).where(PremortemConcern.created_at < cutoff)
    ).all()
    for item in expired:
        db.delete(item)
    if expired:
        db.commit()
    return len(expired)


def pick_action_count(severity: str, impact_level: str) -> int:
    return 2 if "high" in {severity, impact_level} else 1


def deterministic_actions(payload: PremortemConcernCreate) -> list[dict]:
    initiative = payload.initiative_name
    concern = payload.concern_text
    signals = payload.observed_signals or "field reports, support tickets, and discovery calls"

    severity_map = {"low": 1, "medium": 2, "high": 3}
    impact_map = {"low": 2, "medium": 3, "high": 5}

    impact_score_base = min(10, severity_map[payload.severity] + impact_map[payload.impact_level] + 2)
    confidence_base = 8 if payload.severity == "high" else 7 if payload.severity == "medium" else 6
    actions = [
        {
            "title": "Validate concern signal with a 5-account sweep",
            "description": (
                f"Run structured outreach on 5 representative accounts tied to '{initiative}' to validate the concern: "
                f"'{concern}'. Capture evidence from {signals} and identify the top failure mode that could appear in delivery or scale."
            ),
            "owner_role": "Product Manager",
            "due_in_days": 5,
            "impact_score": impact_score_base,
            "effort_score": 3,
            "confidence_score": confidence_base,
            "leading_indicator": "Signal confidence score improves to >= 70% with documented failure pattern.",
        },
        {
            "title": "Launch a two-week risk-offset experiment",
            "description": (
                f"Define and execute a lightweight mitigation experiment for '{initiative}' that directly offsets the concern. "
                "Examples: adjusted onboarding step, support playbook update, or scope guardrail. Review at day 14."
            ),
            "owner_role": "PM + Engineering Lead",
            "due_in_days": 14,
            "impact_score": min(10, impact_score_base + 1),
            "effort_score": 5,
            "confidence_score": max(5, confidence_base - 1),
            "leading_indicator": "Leading KPI trend improves for two consecutive weekly checkpoints.",
        },
    ]
    return actions[: pick_action_count(payload.severity, payload.impact_level)]


def llm_actions(payload: PremortemConcernCreate) -> tuple[list[dict], str]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key:
        return deterministic_actions(payload), "deterministic-fallback"

    prompt = {
        "task": "Generate 1-2 near-term mitigation actions over a 14-day horizon.",
        "concern": payload.model_dump(),
        "output_schema": {
            "actions": [
                {
                    "title": "string",
                    "description": "string",
                    "owner_role": "string",
                    "due_in_days": "int<=14",
                    "impact_score": "1-10",
                    "effort_score": "1-10",
                    "confidence_score": "1-10",
                    "leading_indicator": "string",
                }
            ]
        },
        "constraints": [
            "Return JSON only.",
            "Generate either 1 or 2 actions.",
            "Action must be specific and practical for PM teams.",
        ],
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a PM premortem mitigation planner."},
                {"role": "user", "content": json.dumps(prompt)},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        },
        timeout=20,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    actions = parsed.get("actions", [])
    if not actions:
        return deterministic_actions(payload), "deterministic-fallback"
    return actions[:2], f"llm:{model}"


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        cleanup_expired_concerns(db)


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/decision", response_model=DecisionRead)
def create_decision(payload: DecisionCreate, db: Session = Depends(get_db)) -> Decision:
    decision = Decision(date=payload.date, title=payload.title, context=payload.context)
    decision.constraints = [Constraint(text=item.text) for item in payload.constraints]
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


@app.post("/decision/{decision_id}/assumptions", response_model=List[AssumptionRead])
def add_assumptions(
    decision_id: int, payload: List[AssumptionCreate], db: Session = Depends(get_db)
) -> List[Assumption]:
    decision = db.get(Decision, decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    new_items = [Assumption(text=item.text, decision=decision) for item in payload]
    db.add_all(new_items)
    db.commit()
    for item in new_items:
        db.refresh(item)
    return new_items


@app.post("/decision/{decision_id}/outcome")
def add_outcome(
    decision_id: int, payload: OutcomeCreate, db: Session = Depends(get_db)
) -> dict:
    decision = db.get(Decision, decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    if decision.outcome:
        decision.outcome.text = payload.text
        db.commit()
        db.refresh(decision.outcome)
        outcome = decision.outcome
    else:
        outcome = Outcome(text=payload.text, decision=decision)
        db.add(outcome)
        db.commit()
        db.refresh(outcome)

    return {"id": outcome.id, "text": outcome.text}


@app.get("/decision/{decision_id}/reflection")
def reflect(decision_id: int, db: Session = Depends(get_db)) -> dict:
    decision = db.get(Decision, decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    outcome_text = decision.outcome.text if decision.outcome else ""
    assumption_results = []
    held = []
    contradicted = []

    for assumption in decision.assumptions:
        normalized = assumption.text.strip().lower()
        outcome_normalized = outcome_text.lower()
        is_held = normalized and normalized in outcome_normalized
        assumption_results.append(
            {
                "assumption": assumption.text,
                "held": is_held,
            }
        )
        if is_held:
            held.append(assumption.text)
        else:
            contradicted.append(assumption.text)

    if not decision.outcome:
        summary = "No outcome recorded yet. Add an outcome to compare assumptions."
    elif not decision.assumptions:
        summary = "Outcome recorded, but no assumptions were logged."
    else:
        summary = (
            f"{len(held)} assumptions held, {len(contradicted)} were contradicted."
        )

    return {
        "decision_id": decision.id,
        "title": decision.title,
        "date": decision.date,
        "outcome": decision.outcome.text if decision.outcome else None,
        "assumptions": assumption_results,
        "held_true": held,
        "contradicted": contradicted,
        "summary": summary,
    }


@app.post("/premortem/plan", response_model=PremortemPlanRead)
def create_premortem_plan(
    payload: PremortemConcernCreate, db: Session = Depends(get_db)
) -> PremortemPlanRead:
    cleanup_expired_concerns(db)

    user = db.scalar(select(User).where(User.email == payload.user_email))
    if not user:
        user = User(name=payload.user_name, email=payload.user_email)
        db.add(user)
        db.flush()

    concern = PremortemConcern(
        user=user,
        initiative_name=payload.initiative_name,
        concern_text=payload.concern_text,
        observed_signals=payload.observed_signals,
        severity=payload.severity,
        impact_level=payload.impact_level,
    )
    db.add(concern)
    db.flush()

    try:
        generated_actions, source = llm_actions(payload)
    except Exception:
        generated_actions, source = deterministic_actions(payload), "deterministic-fallback"

    persisted_actions = []
    for action in generated_actions:
        item = MitigationAction(
            concern=concern,
            title=action["title"],
            description=action["description"],
            owner_role=action["owner_role"],
            due_in_days=min(14, max(1, int(action["due_in_days"]))),
            impact_score=min(10, max(1, int(action["impact_score"]))),
            effort_score=min(10, max(1, int(action["effort_score"]))),
            confidence_score=min(10, max(1, int(action["confidence_score"]))),
            leading_indicator=action["leading_indicator"],
        )
        db.add(item)
        persisted_actions.append(item)

    db.commit()
    db.refresh(concern)

    return PremortemPlanRead(
        concern_id=concern.id,
        generated_with=source,
        actions=persisted_actions,
    )
