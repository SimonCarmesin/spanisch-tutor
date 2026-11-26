"""Ein- und Ausgabeformate der API."""

import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from tutor.domain import CefrLevel, ErrorCategory
from tutor.scenarios import FREE_SCENARIO_ID

MAX_USER_TEXT_LENGTH = 1000


class ScenarioOut(BaseModel):
    id: str
    title: str
    learner_goal: str


class StartSessionRequest(BaseModel):
    scenario: str = FREE_SCENARIO_ID
    cefr_level: CefrLevel | None = None


class StartSessionResponse(BaseModel):
    session_id: uuid.UUID
    scenario: ScenarioOut
    cefr_level: CefrLevel
    opening: str


class TurnRequest(BaseModel):
    text: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_USER_TEXT_LENGTH)
    ]


class CorrectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    original: str
    corrected: str
    category: ErrorCategory
    explanation: str


class TurnResponse(BaseModel):
    reply: str
    corrections: list[CorrectionOut]


class CategoryCountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: ErrorCategory
    count: int


class SummaryResponse(BaseModel):
    turns: int
    corrections: list[CorrectionOut]
    by_category: list[CategoryCountOut]


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cefr_level: CefrLevel
    explanation_language: str


class ProfileUpdate(BaseModel):
    cefr_level: CefrLevel
