"""Endpunkte für Szenarien, Gespräche und Beiträge."""

import uuid

from fastapi import APIRouter, status

from tutor.api.deps import ConversationServiceDep, UserIdDep
from tutor.api.v1.schemas import (
    ScenarioOut,
    StartSessionRequest,
    StartSessionResponse,
    SummaryResponse,
    TurnRequest,
    TurnResponse,
)
from tutor.scenarios import SCENARIOS

router = APIRouter(tags=["conversation"])


@router.get("/scenarios")
async def list_scenarios() -> list[ScenarioOut]:
    return [
        ScenarioOut(id=s.id, title=s.title, learner_goal=s.learner_goal) for s in SCENARIOS.values()
    ]


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def start_session(
    body: StartSessionRequest, service: ConversationServiceDep, user_id: UserIdDep
) -> StartSessionResponse:
    started = await service.start_session(
        user_id=user_id, scenario_id=body.scenario, cefr_level=body.cefr_level
    )
    return StartSessionResponse(
        session_id=started.session_id,
        scenario=ScenarioOut(
            id=started.scenario.id,
            title=started.scenario.title,
            learner_goal=started.scenario.learner_goal,
        ),
        cefr_level=started.cefr_level,
        opening=started.opening,
    )


@router.post("/sessions/{session_id}/turns")
async def take_turn(
    session_id: uuid.UUID, body: TurnRequest, service: ConversationServiceDep, user_id: UserIdDep
) -> TurnResponse:
    outcome = await service.take_turn(user_id=user_id, session_id=session_id, text=body.text)
    return TurnResponse.model_validate(outcome, from_attributes=True)


@router.post("/sessions/{session_id}/end")
async def end_session(
    session_id: uuid.UUID, service: ConversationServiceDep, user_id: UserIdDep
) -> SummaryResponse:
    summary = await service.end_session(user_id=user_id, session_id=session_id)
    return SummaryResponse.model_validate(summary, from_attributes=True)
