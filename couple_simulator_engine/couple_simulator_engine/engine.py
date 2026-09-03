"""Public GameEngine orchestrator (spec §6.2). Never prints."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from uuid import uuid4

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.content.catalog import ContentCatalog
from couple_simulator_engine.content.definitions import EventDefinition
from couple_simulator_engine.content.presentation import resolve_text_key
from couple_simulator_engine.enums import PlayerRole, PlayerSex, SessionStatus
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
        partner_b: Player | None = None,
        player_role: PlayerRole | str = PlayerRole.PARTNER_A,
        seed: int | None = None,
        max_events: int | None = None,
    ) -> GameSession:
        config = replace(
            self.config,
            max_events=(
                max_events if max_events is not None else self.config.max_events
            ),
        )
        if partner_b is None:
            state = SimulationState(partner_a=player)
        else:
            state = SimulationState(partner_a=player, partner_b=partner_b)
        state.begin_simulation()
        role = PlayerRole(player_role)
        active_player = (
            state.partner_b if role == PlayerRole.PARTNER_B else state.partner_a
        )
        return GameSession(
            session_id=str(uuid4()),
            player=active_player,
            state=state,
            config=config,
            rng=SeededRNG(seed),
            events_played=0,
            events_played_ids=[],
            event_variables={},
            status=SessionStatus.ACTIVE,
            current_event_id=None,
        )

    def partner_a_answers(
        self, loaded: LoadedGame, event: EventDefinition
    ) -> list[Answer] | None:
        """Partner A answers for ``event``, or None if any question is missing."""
        return loaded.answer_bank.resolve_for_event(event)

    def load_game(self, snapshot: GameSnapshot) -> LoadedGame:
        validate_game_snapshot(snapshot)
        return hydrate_loaded_game(snapshot)

    def export_snapshot(self, loaded: LoadedGame) -> GameSnapshot:
        return export_loaded_game(loaded)

    def select_next_event(
        self, session_or_loaded: GameSession | LoadedGame
    ) -> EventDefinition | None:
        if isinstance(session_or_loaded, LoadedGame):
            return event_selector.select_next_event_for_loaded(
                session_or_loaded, self.catalog
            )
        return event_selector.select_next_event(session_or_loaded, self.catalog)

    def present_event(
        self,
        event: EventDefinition,
        *,
        player_role: PlayerRole | str,
        player_sex: PlayerSex,
    ) -> EventPresentation:
        role_str = (
            player_role.value
            if isinstance(player_role, PlayerRole)
            else str(player_role)
        )
        sex_str = player_sex.value
        questions = [
            QuestionPresentation(
                id=question.id,
                text=resolve_text_key(
                    question.text,
                    player_role=role_str,
                    player_sex=sex_str,
                ),
                options=[
                    OptionPresentation(
                        id=option.id,
                        text=resolve_text_key(
                            option.text,
                            player_role=role_str,
                            player_sex=sex_str,
                        ),
                    )
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
        session_or_loaded: GameSession | LoadedGame,
        event: EventDefinition,
        answers: Sequence[Answer],
    ) -> EventResolution:
        if isinstance(session_or_loaded, LoadedGame):
            loaded = session_or_loaded
            session = loaded.session
            partner_a_answers = (
                self.partner_a_answers(loaded, event)
                if loaded.player_role == PlayerRole.PARTNER_B
                else None
            )
            if session.current_event_id != event.id:
                session.event_variables.clear()
            session.current_event_id = event.id
            return resolve_event(
                session, event, answers, partner_a_answers=partner_a_answers
            )
        session = session_or_loaded
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
