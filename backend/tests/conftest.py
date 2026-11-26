"""Gemeinsame Test-Hilfen: Fake-Modell, Testkonfiguration, App und Datenbank (SQLite)."""

from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from pydantic import SecretStr
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tutor.core.config import Settings
from tutor.db.base import Base
from tutor.db.session import create_engine, create_session_factory
from tutor.domain import ErrorCategory
from tutor.llm.client import ChatMessage
from tutor.llm.schemas import Correction, Keyword, Translation, TutorTurn
from tutor.main import create_app

API_TOKEN = "t" * 32


def make_turn(reply: str = "¡Hola! ¿Qué desea tomar?", *corrections: Correction) -> TutorTurn:
    return TutorTurn(reply=reply, corrections=list(corrections))


def make_correction(
    category: ErrorCategory = ErrorCategory.PRETERITO_INDEFINIDO,
    original: str = "Ayer yo voy al mercado.",
    corrected: str = "Ayer fui al mercado.",
    explanation: str = (
        "Für abgeschlossene Handlungen in der Vergangenheit braucht es das pretérito indefinido. "
        "Von 'ir' heißt es 'fui'."
    ),
) -> Correction:
    return Correction(
        original=original, corrected=corrected, category=category, explanation=explanation
    )


def make_translation(
    translation: str = "Hallo! Was möchtest du trinken?",
    *keywords: tuple[str, str],
) -> Translation:
    return Translation(
        translation=translation,
        keywords=[Keyword(spanish=es, german=de) for es, de in keywords],
    )


class FakeLLM:
    """Ersetzt das Sprachmodell: liefert vorbereitete Antworten, wirft vorbereitete Fehler."""

    def __init__(self, *items: TutorTurn | Exception) -> None:
        self._items = list(items) or [make_turn()]
        self.calls: list[tuple[str, list[ChatMessage]]] = []
        self.before_return: Callable[[], Awaitable[None]] | None = None
        self.translation: Translation | Exception = make_translation()
        self.translate_calls: list[tuple[str, str]] = []

    def script(self, *items: TutorTurn | Exception) -> None:
        """Legt fest, was die nächsten Aufrufe liefern (das letzte Element wiederholt sich)."""
        self._items = list(items)

    async def generate_turn(
        self, *, system_prompt: str, messages: Sequence[ChatMessage]
    ) -> TutorTurn:
        self.calls.append((system_prompt, list(messages)))
        if self.before_return is not None:
            await self.before_return()
        item = self._items.pop(0) if len(self._items) > 1 else self._items[0]
        if isinstance(item, Exception):
            raise item
        return item

    async def translate(self, *, system_prompt: str, text: str) -> Translation:
        self.translate_calls.append((system_prompt, text))
        if isinstance(self.translation, Exception):
            raise self.translation
        return self.translation

    async def aclose(self) -> None:
        return None


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        environment="test",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'test.db'}",
        llm_base_url="http://llm.test",
        llm_api_key=SecretStr("test-key"),
        llm_max_retries=0,
        api_token=SecretStr(API_TOKEN),
        cors_origins=["http://localhost:5173"],
        max_turns_per_session=3,
        history_window=4,
    )


@pytest.fixture
async def session_factory(settings: Settings) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_engine(settings.database_url)

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(dbapi_connection: Any, _: Any) -> None:
        # SQLite prüft Fremdschlüssel nur mit diesem Schalter. Ohne ihn verhalten sich die
        # Tests nachsichtiger als Postgres und übersehen Fehler in der Einfüge-Reihenfolge.
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield create_session_factory(engine)
    await engine.dispose()


@pytest.fixture
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
async def app(
    settings: Settings,
    fake_llm: FakeLLM,
    session_factory: async_sessionmaker[AsyncSession],  # legt die Tabellen an
) -> AsyncIterator[FastAPI]:
    application = create_app(settings, llm_client=fake_llm)
    async with application.router.lifespan_context(application):
        yield application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    """Client mit gültigem Token."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {API_TOKEN}"},
    ) as http_client:
        yield http_client


@pytest.fixture
async def anon_client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    """Client ohne Token."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as http_client:
        yield http_client
