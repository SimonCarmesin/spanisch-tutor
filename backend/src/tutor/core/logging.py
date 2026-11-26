"""Strukturiertes Logging. Texte der Lernenden werden nie geloggt."""

import logging

import structlog


def configure_logging(level: str, *, json_logs: bool) -> None:
    numeric_level = logging.getLevelNamesMapping()[level.upper()]
    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer() if json_logs else structlog.dev.ConsoleRenderer()
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=numeric_level, format="%(message)s", force=True)
