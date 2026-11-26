"""Anbindung des Sprachmodells über einen OpenAI-kompatiblen Endpunkt (das Gateway)."""

import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

import openai
import structlog
from openai import AsyncOpenAI, DefaultAsyncHttpxClient
from openai.types.chat import ChatCompletionMessageParam
from pydantic import ValidationError

from tutor.errors import LLMOutputError, LLMRateLimitError, LLMUnavailableError
from tutor.llm.schemas import TutorTurn

log = structlog.get_logger()

_MAX_ATTEMPTS = 2  # ein Versuch plus ein Wiederholungsversuch bei ungültiger Ausgabe


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: Literal["user", "assistant"]
    content: str


def _to_param(message: ChatMessage) -> ChatCompletionMessageParam:
    if message.role == "user":
        return {"role": "user", "content": message.content}
    return {"role": "assistant", "content": message.content}


def _short(text: str, limit: int = 300) -> str:
    return text if len(text) <= limit else text[:limit] + "…"


def _raw_content(body: object) -> str:
    """Holt den Text der Modellantwort aus der rohen Antwort, ohne bei Abweichungen zu scheitern."""
    try:
        content = body["choices"][0]["message"]["content"]  # type: ignore[index]
    except (KeyError, IndexError, TypeError):
        return ""
    return content if isinstance(content, str) else ""


class LLMClient(Protocol):
    """Schnittstelle, von der die Fachlogik abhängt. Tests ersetzen sie durch ein Fake."""

    async def generate_turn(
        self, *, system_prompt: str, messages: Sequence[ChatMessage]
    ) -> TutorTurn: ...

    async def aclose(self) -> None: ...


class OpenAICompatibleClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_retries: int,
        http_client: DefaultAsyncHttpxClient | None = None,
    ) -> None:
        self._model = model
        self._client = AsyncOpenAI(
            base_url=f"{base_url.rstrip('/')}/v1",
            api_key=api_key,
            timeout=timeout_seconds,
            max_retries=max_retries,
            http_client=http_client,
        )

    async def generate_turn(
        self, *, system_prompt: str, messages: Sequence[ChatMessage]
    ) -> TutorTurn:
        payload: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            *(_to_param(m) for m in messages),
        ]
        last_problem = ""
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            started = time.perf_counter()
            try:
                # with_raw_response: Bei ungültiger Ausgabe brauchen wir den Rohtext,
                # damit das Modell im Wiederholungsversuch sieht, was es falsch gemacht hat.
                raw = await self._client.chat.completions.with_raw_response.parse(
                    model=self._model,
                    messages=payload,
                    response_format=TutorTurn,
                    temperature=0.7,
                )
                completion = raw.parse()
            except ValidationError as exc:
                last_problem = "; ".join(
                    f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()
                )
                log.warning("llm_invalid_output", attempt=attempt, problem=last_problem)
                payload = [
                    *payload,
                    {"role": "assistant", "content": _raw_content(raw.http_response.json())},
                    {
                        "role": "user",
                        "content": (
                            "Deine letzte Ausgabe war ungültig (" + last_problem + "). "
                            "Erzeuge sie neu und halte alle Regeln aus der Anweisung ein."
                        ),
                    },
                ]
                continue
            except openai.RateLimitError as exc:
                raise LLMRateLimitError("Das Sprachmodell ist gerade ausgelastet") from exc
            except openai.APIStatusError as exc:
                # Das Gateway hat geantwortet, aber mit Fehler (zum Beispiel 401, 404, 400).
                # Statuscode und Fehlermeldung loggen, nie den Text der Lernenden.
                log.error(
                    "llm_status_error",
                    status_code=exc.status_code,
                    error=_short(exc.message),
                    request_id=exc.request_id,
                )
                raise LLMUnavailableError("Das Sprachmodell ist nicht erreichbar") from exc
            except openai.APIConnectionError as exc:
                # Keine Antwort: falsche Adresse, Dienst aus, Zeitüberschreitung
                log.error("llm_connection_error", error=_short(str(exc.__cause__ or exc)))
                raise LLMUnavailableError("Das Sprachmodell ist nicht erreichbar") from exc
            except (openai.LengthFinishReasonError, openai.ContentFilterFinishReasonError) as exc:
                raise LLMOutputError("Das Sprachmodell lieferte keine verwertbare Antwort") from exc

            parsed = completion.choices[0].message.parsed
            if parsed is None:
                raise LLMOutputError("Das Sprachmodell lieferte keine verwertbare Antwort")
            usage = completion.usage
            log.info(
                "llm_call",
                model=self._model,
                attempt=attempt,
                latency_ms=round((time.perf_counter() - started) * 1000),
                prompt_tokens=usage.prompt_tokens if usage else None,
                completion_tokens=usage.completion_tokens if usage else None,
            )
            return parsed

        raise LLMOutputError(f"Ungültige Ausgabe des Sprachmodells: {last_problem}")

    async def aclose(self) -> None:
        await self._client.close()
