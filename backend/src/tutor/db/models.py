"""Datenbankmodelle. Alle Tabellen tragen eine Nutzer-ID (Mehrbenutzerbetrieb bleibt möglich)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tutor.db.base import Base
from tutor.domain import CefrLevel

_NOW = text("CURRENT_TIMESTAMP")


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), default=_utcnow, server_default=_NOW)


class LearnerProfile(Base):
    __tablename__ = "learner_profile"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(64), unique=True)
    cefr_level: Mapped[str] = mapped_column(String(2), default=CefrLevel.A1.value)
    explanation_language: Mapped[str] = mapped_column(String(8), default="de")
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, server_default=_NOW
    )


class TutorSession(Base):
    __tablename__ = "tutor_session"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    scenario: Mapped[str] = mapped_column(String(32))
    cefr_level: Mapped[str] = mapped_column(String(2))
    started_at: Mapped[datetime] = _created_at()
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class Message(Base):
    __tablename__ = "message"
    __table_args__ = (
        UniqueConstraint("session_id", "position", name="uq_message_session_position"),
        CheckConstraint("role IN ('user', 'assistant')", name="role_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tutor_session.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int]
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = _created_at()
    # Übersetzung auf Abruf (FR-22, ADR-7), nur für Beiträge der Gegenseite
    translation: Mapped[str | None] = mapped_column(Text, default=None)
    translation_keywords: Mapped[list[dict[str, str]] | None] = mapped_column(JSON, default=None)

    # Die Beziehung sagt SQLAlchemy, dass die Session vor der Nachricht eingefügt werden muss.
    # Ohne sie ist die Reihenfolge innerhalb eines Commits nicht festgelegt.
    session: Mapped[TutorSession] = relationship()


class ErrorLog(Base):
    __tablename__ = "error_log"
    __table_args__ = (Index("ix_error_log_user_category", "user_id", "category"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(64))
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tutor_session.id", ondelete="CASCADE"), index=True
    )
    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("message.id", ondelete="CASCADE"))
    category: Mapped[str] = mapped_column(String(32))
    original: Mapped[str] = mapped_column(Text)
    corrected: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = _created_at()

    session: Mapped[TutorSession] = relationship()
    message: Mapped[Message] = relationship()
