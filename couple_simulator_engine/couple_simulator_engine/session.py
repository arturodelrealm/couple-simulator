"""In-memory session types and engine DTOs (no persistence)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.enums import SessionStatus
from couple_simulator_engine.player import Player
from couple_simulator_engine.rng import SeededRNG
from couple_simulator_engine.state import SimulationState


@dataclass
class RecordedAnswer:
    event_id: str
    question_id: str
    option_id: str
    state_snapshot: dict[str, Any] | None = None


@dataclass
class Answer:
    question_id: str
    option_id: str


@dataclass
class TimelineEntry:
    title: str
    category: str
    age: int
    description: str | None = None


@dataclass
class ClientAction:
    type: str
    args: dict[str, Any]


@dataclass
class OptionPresentation:
    id: str
    text: str


@dataclass
class QuestionPresentation:
    id: str
    text: str
    options: list[OptionPresentation]


@dataclass
class EventPresentation:
    event_id: str
    title: str
    description: str | None
    questions: list[QuestionPresentation]


@dataclass
class EventResolution:
    event_id: str
    applied_outcome_ids: list[str]
    client_actions: list[ClientAction]
    state: SimulationState
    answers_recorded: list[Answer]
    game_finished: bool


@dataclass
class EndCheck:
    finished: bool
    reason: str | None = None


@dataclass
class GameSummary:
    final_state: SimulationState
    timeline: list[TimelineEntry]
    events_played: int
    end_reason: str | None


@dataclass
class GameSession:
    session_id: str
    player: Player
    state: SimulationState
    config: GameConfig
    rng: SeededRNG
    events_played: int = 0
    events_played_ids: list[str] = field(default_factory=list)
    timeline: list[TimelineEntry] = field(default_factory=list)
    answers: list[RecordedAnswer] = field(default_factory=list)
    event_variables: dict[str, Any] = field(default_factory=dict)
    status: SessionStatus = SessionStatus.ACTIVE
    end_reason: str | None = None
    current_event_id: str | None = None
