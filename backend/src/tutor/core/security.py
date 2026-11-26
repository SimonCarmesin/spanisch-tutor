"""Authentifizierung per statischem Bearer-Token (Einzelnutzerbetrieb)."""

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from tutor.core.config import Settings

_bearer = HTTPBearer(auto_error=False)


async def require_api_token(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> None:
    settings: Settings = request.app.state.settings
    expected = settings.api_token.get_secret_value().encode()
    if credentials is None or not secrets.compare_digest(
        credentials.credentials.encode(), expected
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiges oder fehlendes Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
