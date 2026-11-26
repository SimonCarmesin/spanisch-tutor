"""Abhängigkeiten der Endpunkte (Dependency Injection von FastAPI)."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tutor.core.config import Settings
from tutor.llm.client import LLMClient
from tutor.services.conversation import ConversationService


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        yield session


DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_llm(request: Request) -> LLMClient:
    llm: LLMClient = request.app.state.llm
    return llm


LLMDep = Annotated[LLMClient, Depends(get_llm)]


def get_user_id(settings: SettingsDep) -> str:
    """Einzelnutzerbetrieb: alle Anfragen gehören dem Standardnutzer."""
    return settings.default_user_id


UserIdDep = Annotated[str, Depends(get_user_id)]


def get_conversation_service(
    session: DbSessionDep, llm: LLMDep, settings: SettingsDep
) -> ConversationService:
    return ConversationService(session, llm, settings)


ConversationServiceDep = Annotated[ConversationService, Depends(get_conversation_service)]
