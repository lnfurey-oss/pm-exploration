from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False)

    constraints: Mapped[List[Constraint]] = relationship(
        back_populates="decision", cascade="all, delete-orphan"
    )
    assumptions: Mapped[List[Assumption]] = relationship(
        back_populates="decision", cascade="all, delete-orphan"
    )
    outcome: Mapped[Optional[Outcome]] = relationship(
        back_populates="decision", cascade="all, delete-orphan", uselist=False
    )


class Constraint(Base):
    __tablename__ = "constraints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    decision_id: Mapped[int] = mapped_column(ForeignKey("decisions.id"), nullable=False)

    decision: Mapped[Decision] = relationship(back_populates="constraints")


class Assumption(Base):
    __tablename__ = "assumptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    decision_id: Mapped[int] = mapped_column(ForeignKey("decisions.id"), nullable=False)

    decision: Mapped[Decision] = relationship(back_populates="assumptions")


class Outcome(Base):
    __tablename__ = "outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    decision_id: Mapped[int] = mapped_column(
        ForeignKey("decisions.id"), nullable=False, unique=True
    )

    decision: Mapped[Decision] = relationship(back_populates="outcome")


class ConstraintCreate(BaseModel):
    text: str


class AssumptionCreate(BaseModel):
    text: str


class OutcomeCreate(BaseModel):
    text: str


class DecisionCreate(BaseModel):
    date: date
    title: str
    context: str
    constraints: List[ConstraintCreate] = []


class ConstraintRead(BaseModel):
    id: int
    text: str

    class Config:
        from_attributes = True


class AssumptionRead(BaseModel):
    id: int
    text: str

    class Config:
        from_attributes = True


class OutcomeRead(BaseModel):
    id: int
    text: str

    class Config:
        from_attributes = True


class DecisionRead(BaseModel):
    id: int
    date: date
    title: str
    context: str
    constraints: List[ConstraintRead]
    assumptions: List[AssumptionRead]
    outcome: Optional[OutcomeRead]

    class Config:
        from_attributes = True
