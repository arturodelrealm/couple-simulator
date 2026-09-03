from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.shared.enums import PlayerRole


class SimulationRunCreate(BaseModel):
    player_role: PlayerRole
    seed: int | None = None
    max_events: int | None = Field(default=None, ge=1)


class HousingRead(BaseModel):
    place: str
    type: str
    quality: str


class MascotRead(BaseModel):
    species: str
    name: str


class SimulationStateRead(BaseModel):
    age: int
    compatibility: int
    finances: int
    quality_of_life: int
    children: int
    wellness: int
    housing: HousingRead
    mascot: MascotRead | None
    tags: dict[str, Any] = Field(default_factory=dict)
    life_stage: str
    relationship_status: str


class SimulationAnswerRead(BaseModel):
    event_id: str
    question_id: str
    option_id: str


class TimelineEntryRead(BaseModel):
    title: str
    category: str
    age: int
    description: str | None = None


class SimulationRunCreated(BaseModel):
    run_id: UUID
    player_role: str
    status: str
    state: SimulationStateRead
    events_played: int


class SimulationRunDetail(SimulationRunCreated):
    timeline: list[TimelineEntryRead]
    answers: list[SimulationAnswerRead]
    current_event_id: str | None = None
    rng_seed: int
    run_number: int


class SimulationRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: UUID
    player_role: str
    status: str
    created_at: datetime | None = None
    run_number: int


class OptionPresentationRead(BaseModel):
    id: str
    text: str


class QuestionPresentationRead(BaseModel):
    id: str
    text: str
    options: list[OptionPresentationRead]


class EventPresentationRead(BaseModel):
    event_id: str
    title: str
    description: str | None = None
    questions: list[QuestionPresentationRead]


class CurrentEventRead(BaseModel):
    run_id: UUID
    event: EventPresentationRead


class EventAnswerItem(BaseModel):
    question_id: str
    option_id: str


class EventAnswersSubmit(BaseModel):
    answers: list[EventAnswerItem]


class ClientActionRead(BaseModel):
    type: str
    args: dict[str, Any]


class EventAnswersSubmitted(BaseModel):
    run_id: UUID
    status: str
    state: SimulationStateRead
    events_played: int
    client_actions: list[ClientActionRead]
    game_finished: bool
