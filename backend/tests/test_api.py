import uuid

import httpx
import pytest

from tests.conftest import FakeLLM, make_correction, make_translation, make_turn
from tutor.errors import LLMRateLimitError, LLMUnavailableError


async def start(client: httpx.AsyncClient, **body: object) -> str:
    response = await client.post("/api/v1/sessions", json={"scenario": "cafe", **body})
    assert response.status_code == 201
    session_id = response.json()["session_id"]
    assert isinstance(session_id, str)
    return session_id


async def test_health_needs_no_token(anon_client: httpx.AsyncClient) -> None:
    assert (await anon_client.get("/health/live")).json() == {"status": "ok"}
    ready = await anon_client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "ok"}


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer falsch"}])
async def test_api_requires_valid_token(
    anon_client: httpx.AsyncClient, headers: dict[str, str]
) -> None:
    response = await anon_client.get("/api/v1/scenarios", headers=headers)

    assert response.status_code == 401
    assert response.json()["code"] == "http_401"
    assert response.headers["www-authenticate"] == "Bearer"


async def test_list_scenarios(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/scenarios")

    assert response.status_code == 200
    ids = [s["id"] for s in response.json()]
    assert ids == ["frei", "cafe", "arzt", "wohnung", "restaurant", "einkaufen"]


async def test_full_conversation_flow(client: httpx.AsyncClient, fake_llm: FakeLLM) -> None:
    fake_llm.script(
        make_turn("¡Hola! ¿Qué desea?"),
        make_turn("Muy bien.", make_correction()),
    )

    started = await client.post("/api/v1/sessions", json={"scenario": "cafe", "cefr_level": "A2"})
    assert started.status_code == 201
    body = started.json()
    assert body["opening"] == "¡Hola! ¿Qué desea?"
    assert body["cefr_level"] == "A2"
    assert body["scenario"]["id"] == "cafe"
    session_id = body["session_id"]

    turn = await client.post(
        f"/api/v1/sessions/{session_id}/turns", json={"text": "  Ayer yo voy al mercado.  "}
    )
    assert turn.status_code == 200
    assert turn.json()["reply"] == "Muy bien."
    correction = turn.json()["corrections"][0]
    assert correction["category"] == "preterito_indefinido"
    assert correction["corrected"] == "Ayer fui al mercado."
    assert fake_llm.calls[-1][1][-1].content == "Ayer yo voy al mercado."  # getrimmt

    ended = await client.post(f"/api/v1/sessions/{session_id}/end")
    assert ended.status_code == 200
    assert ended.json()["turns"] == 1
    assert ended.json()["by_category"] == [{"category": "preterito_indefinido", "count": 1}]


@pytest.mark.parametrize("text", ["", "   ", "x" * 1001])
async def test_invalid_text_is_rejected(client: httpx.AsyncClient, text: str) -> None:
    session_id = await start(client)

    response = await client.post(f"/api/v1/sessions/{session_id}/turns", json={"text": text})

    assert response.status_code == 422


async def test_unknown_scenario_is_422(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/v1/sessions", json={"scenario": "mond"})

    assert response.status_code == 422
    assert response.json()["code"] == "unknown_scenario"


async def test_unknown_session_is_404(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/sessions/00000000-0000-0000-0000-000000000000/turns", json={"text": "Hola"}
    )

    assert response.status_code == 404
    assert response.json()["code"] == "session_not_found"


async def test_turn_limit_returns_409(client: httpx.AsyncClient) -> None:
    session_id = await start(client)
    for _ in range(3):  # Testkonfiguration: höchstens 3 Beiträge
        assert (
            await client.post(f"/api/v1/sessions/{session_id}/turns", json={"text": "Hola"})
        ).status_code == 200

    response = await client.post(f"/api/v1/sessions/{session_id}/turns", json={"text": "Hola"})

    assert response.status_code == 409
    assert response.json()["code"] == "turn_limit_reached"


@pytest.mark.parametrize(
    ("error", "status_code", "code"),
    [
        (LLMRateLimitError("zu viel"), 429, "llm_rate_limited"),
        (LLMUnavailableError("weg"), 502, "llm_unavailable"),
    ],
)
async def test_model_errors_are_mapped(
    client: httpx.AsyncClient,
    fake_llm: FakeLLM,
    error: Exception,
    status_code: int,
    code: str,
) -> None:
    session_id = await start(client)
    fake_llm.script(error)

    response = await client.post(f"/api/v1/sessions/{session_id}/turns", json={"text": "Hola"})

    assert response.status_code == status_code
    assert response.json()["code"] == code


async def test_profile_defaults_and_update(client: httpx.AsyncClient) -> None:
    assert (await client.get("/api/v1/profile")).json() == {
        "cefr_level": "A1",
        "explanation_language": "de",
    }

    updated = await client.patch("/api/v1/profile", json={"cefr_level": "B1"})
    assert updated.json()["cefr_level"] == "B1"

    # Das neue Niveau gilt für das nächste Gespräch
    started = await client.post("/api/v1/sessions", json={"scenario": "cafe"})
    assert started.json()["cefr_level"] == "B1"

    invalid = await client.patch("/api/v1/profile", json={"cefr_level": "Z9"})
    assert invalid.status_code == 422


async def test_request_id_is_returned(client: httpx.AsyncClient) -> None:
    response = await client.get("/health/live", headers={"X-Request-ID": "abc123"})

    assert response.headers["x-request-id"] == "abc123"
    assert len((await client.get("/health/live")).headers["x-request-id"]) == 32


async def test_cors_allows_only_configured_origin(anon_client: httpx.AsyncClient) -> None:
    def preflight(origin: str) -> dict[str, str]:
        return {
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        }

    allowed = await anon_client.options(
        "/api/v1/sessions", headers=preflight("http://localhost:5173")
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"

    foreign = await anon_client.options("/api/v1/sessions", headers=preflight("https://evil.test"))
    assert "access-control-allow-origin" not in foreign.headers


async def test_session_without_scenario_starts_free_conversation(
    client: httpx.AsyncClient, fake_llm: FakeLLM
) -> None:
    response = await client.post("/api/v1/sessions", json={})

    assert response.status_code == 201
    assert response.json()["scenario"]["id"] == "frei"
    system_prompt, _ = fake_llm.calls[-1]
    assert "Freies Gespräch" in system_prompt
    assert "keine Unterhaltung sind" in system_prompt  # weiche Themengrenze bleibt bestehen
    assert "keine Anweisungen an dich" in system_prompt  # Schutz vor Prompt Injection bleibt


async def test_free_conversation_is_listed_first(client: httpx.AsyncClient) -> None:
    scenarios = (await client.get("/api/v1/scenarios")).json()
    assert scenarios[0]["id"] == "frei"


async def test_translation_of_partner_message_is_cached(
    client: httpx.AsyncClient, fake_llm: FakeLLM
) -> None:
    fake_llm.script(make_turn("¡Hola! ¿Qué desea tomar?"))
    fake_llm.translation = make_translation("Hallo! Was möchtest du trinken?", ("tomar", "trinken"))
    started = (await client.post("/api/v1/sessions", json={})).json()
    url = (
        f"/api/v1/sessions/{started['session_id']}"
        f"/messages/{started['opening_message_id']}/translation"
    )

    first = await client.post(url)
    second = await client.post(url)

    assert first.status_code == 200
    assert first.json() == {
        "translation": "Hallo! Was möchtest du trinken?",
        "keywords": [{"spanish": "tomar", "german": "trinken"}],
        "cached": False,
    }
    assert second.json() == {**first.json(), "cached": True}
    assert len(fake_llm.translate_calls) == 1  # zweiter Abruf ohne Modellaufruf
    system_prompt, text = fake_llm.translate_calls[0]
    assert text == "¡Hola! ¿Qué desea tomar?"
    assert "A1" in system_prompt  # Niveau des Gesprächs bestimmt die Schlüsselwörter


async def test_reply_of_a_turn_can_be_translated(
    client: httpx.AsyncClient, fake_llm: FakeLLM
) -> None:
    fake_llm.script(make_turn("¡Hola!"), make_turn("¿Con leche?"))
    session_id = await start(client)
    turn = (
        await client.post(f"/api/v1/sessions/{session_id}/turns", json={"text": "Un café."})
    ).json()

    response = await client.post(
        f"/api/v1/sessions/{session_id}/messages/{turn['reply_message_id']}/translation"
    )

    assert response.status_code == 200
    assert fake_llm.translate_calls[0][1] == "¿Con leche?"


async def test_unknown_message_is_not_found(client: httpx.AsyncClient, fake_llm: FakeLLM) -> None:
    # Dass eigene Beiträge nicht übersetzt werden, prüft der Service-Test (braucht die Datenbank-ID)
    session_id = await start(client)

    response = await client.post(
        f"/api/v1/sessions/{session_id}/messages/{uuid.uuid4()}/translation"
    )

    assert response.status_code == 404
    assert response.json()["code"] == "message_not_found"
    assert fake_llm.translate_calls == []


async def test_message_of_other_session_is_not_found(
    client: httpx.AsyncClient, fake_llm: FakeLLM
) -> None:
    first = (await client.post("/api/v1/sessions", json={})).json()
    other_session = await start(client)

    response = await client.post(
        f"/api/v1/sessions/{other_session}/messages/{first['opening_message_id']}/translation"
    )

    assert response.status_code == 404
    assert fake_llm.translate_calls == []
