"""Fachlogik der Gespräche.

Wichtig: Der Modellaufruf läuft ohne offene Datenbanktransaktion, und geschrieben wird erst
danach in einer einzigen Transaktion. Schlägt der Aufruf fehl, bleibt kein halber Zustand zurück.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from tutor.core.config import Settings
from tutor.db.models import ErrorLog, Message, TutorSession
from tutor.domain import CefrLevel, ErrorCategory, Role
from tutor.errors import (
    ConcurrentTurnError,
    MessageNotFoundError,
    MessageNotTranslatableError,
    SessionClosedError,
    SessionNotFoundError,
    TurnLimitReachedError,
)
from tutor.llm.client import ChatMessage, LLMClient
from tutor.llm.prompts import OPENING_USER_MESSAGE, build_system_prompt, build_translation_prompt
from tutor.llm.schemas import Correction, Keyword
from tutor.scenarios import Scenario, get_scenario
from tutor.services.profile import get_or_create_profile


@dataclass(frozen=True, slots=True)
class StartedSession:
    session_id: uuid.UUID
    scenario: Scenario
    cefr_level: CefrLevel
    opening: str
    opening_message_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class TurnOutcome:
    reply: str
    reply_message_id: uuid.UUID
    corrections: list[Correction]


@dataclass(frozen=True, slots=True)
class TranslationOutcome:
    translation: str
    keywords: list[Keyword]
    cached: bool


@dataclass(frozen=True, slots=True)
class CorrectionRecord:
    original: str
    corrected: str
    category: ErrorCategory
    explanation: str


@dataclass(frozen=True, slots=True)
class CategoryCount:
    category: ErrorCategory
    count: int


@dataclass(frozen=True, slots=True)
class SessionSummary:
    turns: int
    corrections: list[CorrectionRecord]
    by_category: list[CategoryCount]


def _is_position_conflict(exc: IntegrityError) -> bool:
    """Erkennt die Verletzung der Regel "eine Nachricht pro Position" (Postgres und SQLite)."""
    detail = str(exc.orig)
    return "uq_message_session_position" in detail or (
        "UNIQUE" in detail and "message.session_id, message.position" in detail
    )


class ConversationService:
    def __init__(self, session: AsyncSession, llm: LLMClient, settings: Settings) -> None:
        self._session = session
        self._llm = llm
        self._settings = settings

    async def start_session(
        self, *, user_id: str, scenario_id: str, cefr_level: CefrLevel | None
    ) -> StartedSession:
        scenario = get_scenario(scenario_id)
        if cefr_level is None:
            profile = await get_or_create_profile(self._session, user_id)
            level = CefrLevel(profile.cefr_level)
        else:
            level = cefr_level
        await self._session.commit()  # Lesezugriffe beenden, bevor das Modell aufgerufen wird

        turn = await self._llm.generate_turn(
            system_prompt=build_system_prompt(scenario, level),
            messages=[ChatMessage(role="user", content=OPENING_USER_MESSAGE)],
        )

        tutor_session = TutorSession(
            id=uuid.uuid4(), user_id=user_id, scenario=scenario.id, cefr_level=level.value
        )
        self._session.add(tutor_session)
        opening_message_id = uuid.uuid4()
        self._session.add(
            Message(
                id=opening_message_id,
                session_id=tutor_session.id,
                position=0,
                role=Role.ASSISTANT.value,
                content=turn.reply,
            )
        )
        await self._session.commit()
        return StartedSession(
            session_id=tutor_session.id,
            scenario=scenario,
            cefr_level=level,
            opening=turn.reply,
            opening_message_id=opening_message_id,
        )

    async def take_turn(self, *, user_id: str, session_id: uuid.UUID, text: str) -> TurnOutcome:
        tutor_session = await self._get_open_session(user_id, session_id)
        scenario = get_scenario(tutor_session.scenario)
        level = CefrLevel(tutor_session.cefr_level)

        total_messages = await self._count_messages(session_id)
        user_turns = await self._count_messages(session_id, role=Role.USER)
        if user_turns >= self._settings.max_turns_per_session:
            raise TurnLimitReachedError("Die maximale Gesprächslänge ist erreicht")
        history = await self._recent_history(session_id)
        await self._session.commit()  # Lesezugriffe beenden, bevor das Modell aufgerufen wird

        turn = await self._llm.generate_turn(
            system_prompt=build_system_prompt(scenario, level),
            messages=[*history, ChatMessage(role="user", content=text)],
        )

        user_message = Message(
            id=uuid.uuid4(),
            session_id=session_id,
            position=total_messages,
            role=Role.USER.value,
            content=text,
        )
        self._session.add(user_message)
        reply_message_id = uuid.uuid4()
        self._session.add(
            Message(
                id=reply_message_id,
                session_id=session_id,
                position=total_messages + 1,
                role=Role.ASSISTANT.value,
                content=turn.reply,
            )
        )
        self._session.add_all(
            ErrorLog(
                user_id=user_id,
                session_id=session_id,
                message_id=user_message.id,
                category=c.category.value,
                original=c.original,
                corrected=c.corrected,
                explanation=c.explanation,
            )
            for c in turn.corrections
        )
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if _is_position_conflict(exc):
                # Zwei gleichzeitige Beiträge zur selben Position: der zweite verliert
                raise ConcurrentTurnError(
                    "Es läuft bereits ein Beitrag in diesem Gespräch"
                ) from exc
            raise  # andere Verletzungen sind Programmfehler und dürfen nicht verschleiert werden
        return TurnOutcome(
            reply=turn.reply, reply_message_id=reply_message_id, corrections=turn.corrections
        )

    async def translate_message(
        self, *, user_id: str, session_id: uuid.UUID, message_id: uuid.UUID
    ) -> TranslationOutcome:
        """Übersetzt einen Beitrag der Gegenseite ins Deutsche (FR-22) und speichert das Ergebnis.

        Auch für beendete Gespräche erlaubt, damit man sie nachträglich durchgehen kann.
        """
        tutor_session = await self._get_session(user_id, session_id)
        message = await self._session.scalar(
            select(Message).where(Message.id == message_id, Message.session_id == session_id)
        )
        if message is None:
            raise MessageNotFoundError("Nachricht nicht gefunden")
        if message.role != Role.ASSISTANT.value:
            raise MessageNotTranslatableError("Übersetzt werden nur Beiträge der Gegenseite")
        if message.translation is not None:
            # Bereits übersetzt: kein zweiter Modellaufruf (ADR-7)
            return TranslationOutcome(
                translation=message.translation,
                keywords=[Keyword(**k) for k in message.translation_keywords or []],
                cached=True,
            )
        text = message.content
        level = CefrLevel(tutor_session.cefr_level)
        await self._session.commit()  # Lesezugriffe beenden, bevor das Modell aufgerufen wird

        result = await self._llm.translate(system_prompt=build_translation_prompt(level), text=text)

        message.translation = result.translation
        message.translation_keywords = [k.model_dump() for k in result.keywords]
        await self._session.commit()
        return TranslationOutcome(
            translation=result.translation, keywords=result.keywords, cached=False
        )

    async def end_session(self, *, user_id: str, session_id: uuid.UUID) -> SessionSummary:
        tutor_session = await self._get_session(user_id, session_id)
        if tutor_session.ended_at is None:
            tutor_session.ended_at = datetime.now(UTC)
            await self._session.commit()
        return await self._summarize(session_id)

    async def _get_session(self, user_id: str, session_id: uuid.UUID) -> TutorSession:
        tutor_session = await self._session.scalar(
            select(TutorSession).where(
                TutorSession.id == session_id, TutorSession.user_id == user_id
            )
        )
        if tutor_session is None:
            raise SessionNotFoundError("Gespräch nicht gefunden")
        return tutor_session

    async def _get_open_session(self, user_id: str, session_id: uuid.UUID) -> TutorSession:
        tutor_session = await self._get_session(user_id, session_id)
        if tutor_session.ended_at is not None:
            raise SessionClosedError("Das Gespräch ist bereits beendet")
        return tutor_session

    async def _count_messages(self, session_id: uuid.UUID, *, role: Role | None = None) -> int:
        statement = (
            select(func.count()).select_from(Message).where(Message.session_id == session_id)
        )
        if role is not None:
            statement = statement.where(Message.role == role.value)
        return await self._session.scalar(statement) or 0

    async def _recent_history(self, session_id: uuid.UUID) -> list[ChatMessage]:
        rows = await self._session.scalars(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.position.desc())
            .limit(self._settings.history_window)
        )
        window = list(reversed(rows.all()))
        history = [ChatMessage(role=Role(m.role).value, content=m.content) for m in window]
        # Viele Anbieter verlangen, dass der Verlauf mit einer Nutzernachricht beginnt.
        # Damit bleibt der Modellwechsel über das Gateway (ADR-2) ohne Codeänderung möglich.
        if window and window[0].position == 0:
            # Gesprächsanfang im Fenster: die damals gesendete Eröffnungsanweisung voranstellen
            return [ChatMessage(role="user", content=OPENING_USER_MESSAGE), *history]
        if history and history[0].role == "assistant":
            # Anfang aus dem Fenster gefallen: angeschnittene Antwort ohne Frage weglassen
            return history[1:]
        return history

    async def _summarize(self, session_id: uuid.UUID) -> SessionSummary:
        turns = await self._count_messages(session_id, role=Role.USER)
        rows = await self._session.scalars(
            select(ErrorLog).where(ErrorLog.session_id == session_id).order_by(ErrorLog.created_at)
        )
        corrections = [
            CorrectionRecord(
                original=r.original,
                corrected=r.corrected,
                category=ErrorCategory(r.category),
                explanation=r.explanation,
            )
            for r in rows.all()
        ]
        counts: dict[ErrorCategory, int] = {}
        for correction in corrections:
            counts[correction.category] = counts.get(correction.category, 0) + 1
        by_category = [
            CategoryCount(category=category, count=count)
            for category, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        ]
        return SessionSummary(turns=turns, corrections=corrections, by_category=by_category)
