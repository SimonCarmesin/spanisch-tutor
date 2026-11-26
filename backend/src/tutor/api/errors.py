"""Einheitliches Fehlerformat: {"code": "...", "message": "..."}."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from tutor.errors import (
    ConcurrentTurnError,
    LLMOutputError,
    LLMRateLimitError,
    LLMUnavailableError,
    MessageNotFoundError,
    MessageNotTranslatableError,
    SessionClosedError,
    SessionNotFoundError,
    TurnLimitReachedError,
    TutorError,
    UnknownScenarioError,
)

_STATUS_BY_ERROR: dict[type[TutorError], int] = {
    UnknownScenarioError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    SessionNotFoundError: status.HTTP_404_NOT_FOUND,
    MessageNotFoundError: status.HTTP_404_NOT_FOUND,
    MessageNotTranslatableError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    SessionClosedError: status.HTTP_409_CONFLICT,
    TurnLimitReachedError: status.HTTP_409_CONFLICT,
    ConcurrentTurnError: status.HTTP_409_CONFLICT,
    LLMRateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
    LLMUnavailableError: status.HTTP_502_BAD_GATEWAY,
    LLMOutputError: status.HTTP_502_BAD_GATEWAY,
}


def _body(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


async def _handle_tutor_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, TutorError)  # noqa: S101 - für den Typchecker
    http_status = _STATUS_BY_ERROR.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(_body(exc.code, str(exc)), status_code=http_status)


async def _handle_http_exception(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)  # noqa: S101 - für den Typchecker
    return JSONResponse(
        _body(f"http_{exc.status_code}", str(exc.detail)),
        status_code=exc.status_code,
        headers=exc.headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(TutorError, _handle_tutor_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
