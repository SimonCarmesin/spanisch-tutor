"""Einstiegspunkt: App-Fabrik. Start mit `uvicorn tutor.main:create_app --factory`."""

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from tutor.api import health
from tutor.api.errors import register_exception_handlers
from tutor.api.v1.router import router as v1_router
from tutor.core.config import Settings, get_settings
from tutor.core.logging import configure_logging
from tutor.db.session import create_engine, create_session_factory
from tutor.llm.client import LLMClient, OpenAICompatibleClient

log = structlog.get_logger()


def create_app(settings: Settings | None = None, llm_client: LLMClient | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, json_logs=settings.environment == "prod")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(settings.database_url)
        llm = llm_client or OpenAICompatibleClient(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key.get_secret_value(),
            model=settings.llm_model,
            translation_model=settings.llm_translation_model,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )
        app.state.settings = settings
        app.state.session_factory = create_session_factory(engine)
        app.state.llm = llm
        log.info("startup", environment=settings.environment, model=settings.llm_model)
        try:
            yield
        finally:
            await llm.aclose()
            await engine.dispose()
            log.info("shutdown")

    app = FastAPI(
        title="Spanisch-Tutor",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if settings.environment == "prod" else "/docs",
        redoc_url=None,
    )

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    if settings.cors_origins:
        # Nur für die Entwicklung mit getrenntem Frontend-Server nötig. Produktiv laufen
        # Frontend und API unter derselben Origin (Ingress), dann bleibt die Liste leer.
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST", "PATCH"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
            expose_headers=["X-Request-ID"],
        )

    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(v1_router)
    return app
