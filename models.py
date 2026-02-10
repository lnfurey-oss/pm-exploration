from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    concerns: Mapped[List[PremortemConcern]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


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


class PremortemConcern(Base):
    __tablename__ = "premortem_concerns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    initiative_name: Mapped[str] = mapped_column(String(200), nullable=False)
    concern_text: Mapped[str] = mapped_column(Text, nullable=False)
    observed_signals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    impact_level: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    user: Mapped[User] = relationship(back_populates="concerns")
    actions: Mapped[List[MitigationAction]] = relationship(
        back_populates="concern", cascade="all, delete-orphan"
    )


class MitigationAction(Base):
    __tablename__ = "mitigation_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    concern_id: Mapped[int] = mapped_column(
        ForeignKey("premortem_concerns.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    owner_role: Mapped[str] = mapped_column(String(120), nullable=False)
    due_in_days: Mapped[int] = mapped_column(Integer, nullable=False)
    impact_score: Mapped[int] = mapped_column(Integer, nullable=False)
    effort_score: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False)
    leading_indicator: Mapped[str] = mapped_column(Text, nullable=False)

    concern: Mapped[PremortemConcern] = relationship(back_populates="actions")


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


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True


class PremortemConcernCreate(BaseModel):
    user_email: EmailStr
    user_name: str = Field(min_length=1, max_length=120)
    initiative_name: str = Field(min_length=3, max_length=200)
    concern_text: str = Field(min_length=10, max_length=2000)
    observed_signals: Optional[str] = Field(default=None, max_length=1000)
    severity: str = Field(pattern="^(low|medium|high)$")
    impact_level: str = Field(pattern="^(low|medium|high)$")


class MitigationActionRead(BaseModel):
    title: str
    description: str
    owner_role: str
    due_in_days: int
    impact_score: int
    effort_score: int
    confidence_score: int
    leading_indicator: str

    class Config:
        from_attributes = True


class PremortemPlanRead(BaseModel):
    concern_id: int
    generated_with: str
    two_week_horizon_days: int = 14
    actions: List[MitigationActionRead]
