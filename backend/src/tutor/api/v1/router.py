"""Alle Endpunkte der Version 1, geschützt durch das API-Token."""

from fastapi import APIRouter, Depends

from tutor.api.v1 import profile, sessions
from tutor.core.security import require_api_token

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_token)])
router.include_router(sessions.router)
router.include_router(profile.router)
