"""Lernerprofil: Niveau und Einstellungen."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from tutor.db.models import LearnerProfile
from tutor.domain import CefrLevel


async def get_or_create_profile(session: AsyncSession, user_id: str) -> LearnerProfile:
    """Liefert das Profil und legt es beim ersten Zugriff an (auch bei gleichzeitigen Anfragen)."""
    statement = select(LearnerProfile).where(LearnerProfile.user_id == user_id)
    profile = await session.scalar(statement)
    if profile is not None:
        return profile

    profile = LearnerProfile(user_id=user_id)
    session.add(profile)
    try:
        await session.commit()
    except IntegrityError:
        # Eine parallele Anfrage war schneller: deren Profil verwenden
        await session.rollback()
        existing = await session.scalar(statement)
        if existing is None:
            raise
        return existing
    return profile


async def update_level(session: AsyncSession, user_id: str, level: CefrLevel) -> LearnerProfile:
    profile = await get_or_create_profile(session, user_id)
    profile.cefr_level = level.value
    await session.commit()
    return profile
