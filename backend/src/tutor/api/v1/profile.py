"""Endpunkte für das Lernerprofil."""

from fastapi import APIRouter

from tutor.api.deps import DbSessionDep, UserIdDep
from tutor.api.v1.schemas import ProfileOut, ProfileUpdate
from tutor.services import profile as profile_service

router = APIRouter(tags=["profile"])


@router.get("/profile")
async def get_profile(session: DbSessionDep, user_id: UserIdDep) -> ProfileOut:
    profile = await profile_service.get_or_create_profile(session, user_id)
    return ProfileOut.model_validate(profile)


@router.patch("/profile")
async def update_profile(
    body: ProfileUpdate, session: DbSessionDep, user_id: UserIdDep
) -> ProfileOut:
    profile = await profile_service.update_level(session, user_id, body.cefr_level)
    return ProfileOut.model_validate(profile)
