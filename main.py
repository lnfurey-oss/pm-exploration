from __future__ import annotations

from typing import Generator, List

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
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
    Outcome,
    OutcomeCreate,
)

DATABASE_URL = "sqlite:///./decisions.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Product Decision Copilot")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


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
