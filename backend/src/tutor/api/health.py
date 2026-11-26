"""Gesundheitsprüfungen für Container und Kubernetes."""

import structlog
from fastapi import APIRouter, Response, status
from sqlalchemy import text

from tutor.api.deps import DbSessionDep

router = APIRouter(prefix="/health", tags=["health"])
log = structlog.get_logger()


@router.get("/live")
async def live() -> dict[str, str]:
    """Der Prozess läuft."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(session: DbSessionDep, response: Response) -> dict[str, str]:
    """Der Dienst kann Anfragen bearbeiten (Datenbank erreichbar)."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        log.exception("readiness_check_failed")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "database_unavailable"}
    return {"status": "ok"}
