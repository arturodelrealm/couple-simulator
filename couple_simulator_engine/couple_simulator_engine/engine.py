"""Public GameEngine orchestrator (spec §6.2). Never prints."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import uuid4

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.content.catalog import ContentCatalog
from couple_simulator_engine.content.definitions import EventDefinition
from couple_simulator_engine.enums import SessionStatus
from couple_simulator_engine.player import Player
from couple_simulator_engine.resolution.event_resolver import resolve_event
from couple_simulator_engine.rng import SeededRNG
from couple_simulator_engine.selection import event_selector
from couple_simulator_engine.session import (
    Answer,
    EndCheck,
    EventPresentation,
    EventResolution,
    GameSession,
    GameSummary,
    OptionPresentation,
    QuestionPresentation,
)
from couple_simulator_engine.snapshot import (
    GameSnapshot,
    LoadedGame,
    export_loaded_game,
    hydrate_loaded_game,
    validate_game_snapshot,
)
from couple_simulator_engine.state import SimulationState

END_REASON_MAX_EVENTS = "max_events"
END_REASON_NO_ELIGIBLE_EVENTS = "no_eligible_events"


class GameEngine:
    def __init__(
        self, catalog: ContentCatalog, config: GameConfig | None = None
    ) -> None:
        self.catalog = catalog
        self.config = config if config is not None else GameConfig()

    def new_session(
        self,
        player: Player,
        *,
        seed: int | None = None,
        max_events: int | None = None,
    ) -> GameSession:
        config = GameConfig(
            max_events=(
                max_events if max_events is not None else self.config.max_events
            )
        )
        state = SimulationState(partner_a=player)
        state.begin_simulation()
        return GameSession(
            session_id=str(uuid4()),
            player=player,
            state=state,
            config=config,
            rng=SeededRNG(seed),
            events_played=0,
            events_played_ids=[],
            event_variables={},
            status=SessionStatus.ACTIVE,
            current_event_id=None,
        )

    def load_game(self, snapshot: GameSnapshot) -> LoadedGame:
        validate_game_snapshot(snapshot)
        return hydrate_loaded_game(snapshot)

    def export_snapshot(self, loaded: LoadedGame) -> GameSnapshot:
        return export_loaded_game(loaded)

    def select_next_event(self, session: GameSession) -> EventDefinition | None:
        return event_selector.select_next_event(session, self.catalog)

    def present_event(self, event: EventDefinition) -> EventPresentation:
        questions = [
            QuestionPresentation(
                id=question.id,
                text=question.text,
                options=[
                    OptionPresentation(id=option.id, text=option.text)
                    for option in question.options
                ],
            )
            for question in event.questions
        ]
        return EventPresentation(
            event_id=event.id,
            title=event.title,
            description=event.description,
            questions=questions,
        )

    def submit_answers(
        self,
        session: GameSession,
        event: EventDefinition,
        answers: Sequence[Answer],
    ) -> EventResolution:
        if session.current_event_id != event.id:
            session.event_variables.clear()
        session.current_event_id = event.id
        return resolve_event(session, event, answers)

    def check_end_conditions(self, session: GameSession) -> EndCheck:
        if session.status == SessionStatus.FINISHED:
            return EndCheck(finished=True, reason=session.end_reason)
        if session.events_played >= session.config.max_events:
            session.status = SessionStatus.FINISHED
            session.end_reason = END_REASON_MAX_EVENTS
            return EndCheck(finished=True, reason=session.end_reason)
        if not event_selector.eligible_events(session, self.catalog):
            session.status = SessionStatus.FINISHED
            session.end_reason = END_REASON_NO_ELIGIBLE_EVENTS
            return EndCheck(finished=True, reason=session.end_reason)
        return EndCheck(finished=False)

    def build_summary(self, session: GameSession) -> GameSummary:
        return GameSummary(
            final_state=session.state,
            timeline=list(session.timeline),
            events_played=session.events_played,
            end_reason=session.end_reason,
        )
