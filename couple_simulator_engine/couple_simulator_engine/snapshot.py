"""RAM DTOs for loading and exporting a game between requests (no persistence)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.content.answers import AnswerBank
from couple_simulator_engine.enums import (
    HousingQuality,
    HousingType,
    LifeStage,
    PlayerSex,
    RelationshipStatus,
    SessionStatus,
)
from couple_simulator_engine.player import Player
from couple_simulator_engine.rng import SeededRNG
from couple_simulator_engine.session import GameSession, RecordedAnswer, TimelineEntry
from couple_simulator_engine.state import Housing, Mascot, SimulationState

PlayerRoleName = Literal["partner_a", "partner_b"]

_VALID_PLAYER_ROLES = frozenset({"partner_a", "partner_b"})
_VALID_RUN_STATUSES = frozenset({SessionStatus.ACTIVE, SessionStatus.FINISHED})


def copy_player(player: Player) -> Player:
    avatar = dict(player.avatar_config) if player.avatar_config is not None else None
    return Player(
        id=player.id,
        name=player.name,
        sex=PlayerSex(player.sex),
        game_age=player.game_age,
        game_relation_happiness=player.game_relation_happiness,
        simulation_age=player.simulation_age,
        simulation_relation_happiness=player.simulation_relation_happiness,
        avatar_config=avatar,
    )


def copy_housing(housing: Housing) -> Housing:
    return Housing(
        place=housing.place,
        type=HousingType(housing.type),
        quality=HousingQuality(housing.quality),
    )


def copy_mascot(mascot: Mascot | None) -> Mascot | None:
    if mascot is None:
        return None
    return Mascot(species=mascot.species, name=mascot.name)


def copy_simulation_state(state: SimulationState) -> SimulationState:
    """Round-trip partners and couple stats (not ``SimulationState.to_dict()``)."""
    return SimulationState(
        partner_a=copy_player(state.partner_a),
        partner_b=copy_player(state.partner_b),
        finances=state.finances,
        quality_of_life=state.quality_of_life,
        children=state.children,
        wellness=state.wellness,
        housing=copy_housing(state.housing),
        mascot=copy_mascot(state.mascot),
        tags=dict(state.tags),
        life_stage=LifeStage(state.life_stage),
        relationship_status=RelationshipStatus(state.relationship_status),
    )


def _copy_timeline(entries: list[TimelineEntry]) -> list[TimelineEntry]:
    return [
        TimelineEntry(
            title=entry.title,
            category=entry.category,
            age=entry.age,
            description=entry.description,
        )
        for entry in entries
    ]


def _copy_answers_omit_state_snapshot(
    answers: list[RecordedAnswer],
) -> list[RecordedAnswer]:
    return [
        RecordedAnswer(
            event_id=item.event_id,
            question_id=item.question_id,
            option_id=item.option_id,
            state_snapshot=None,
        )
        for item in answers
    ]


def _copy_event_variables(event_variables: dict[str, Any]) -> dict[str, Any]:
    return dict(event_variables)


def _session_player_for_role(state: SimulationState, player_role: str) -> Player:
    if player_role == "partner_b":
        return state.partner_b
    return state.partner_a


def session_from_run_snapshot(run: RunSnapshot) -> GameSession:
    state = copy_simulation_state(run.state)
    return GameSession(
        session_id=run.run_id,
        player=_session_player_for_role(state, run.player_role),
        state=state,
        config=GameConfig(max_events=run.max_events),
        rng=SeededRNG(run.rng_seed),
        events_played=run.events_played,
        events_played_ids=list(run.events_played_ids),
        timeline=_copy_timeline(run.timeline),
        answers=_copy_answers_omit_state_snapshot(run.answers),
        event_variables=_copy_event_variables(run.event_variables),
        status=SessionStatus(run.status),
        end_reason=run.end_reason,
        current_event_id=run.current_event_id,
    )


def run_snapshot_from_session(
    session: GameSession,
    *,
    player_role: PlayerRoleName,
    run_number: int,
) -> RunSnapshot:
    return RunSnapshot(
        run_id=session.session_id,
        player_role=player_role,
        run_number=run_number,
        status=SessionStatus(session.status),
        state=copy_simulation_state(session.state),
        rng_seed=session.rng.seed,
        events_played=session.events_played,
        events_played_ids=list(session.events_played_ids),
        timeline=_copy_timeline(session.timeline),
        answers=_copy_answers_omit_state_snapshot(session.answers),
        event_variables=_copy_event_variables(session.event_variables),
        current_event_id=session.current_event_id,
        end_reason=session.end_reason,
        max_events=session.config.max_events,
    )


def copy_run_snapshot(run: RunSnapshot) -> RunSnapshot:
    return RunSnapshot(
        run_id=run.run_id,
        player_role=run.player_role,
        run_number=run.run_number,
        status=SessionStatus(run.status),
        rng_seed=run.rng_seed,
        events_played=run.events_played,
        events_played_ids=list(run.events_played_ids),
        timeline=_copy_timeline(run.timeline),
        answers=_copy_answers_omit_state_snapshot(run.answers),
        event_variables=_copy_event_variables(run.event_variables),
        current_event_id=run.current_event_id,
        end_reason=run.end_reason,
        max_events=run.max_events,
        state=copy_simulation_state(run.state),
    )


def _answers_for_bank(snapshot: GameSnapshot) -> list[RecordedAnswer]:
    collected: list[RecordedAnswer] = []
    for run in snapshot.partner_a_runs:
        collected.extend(run.answers)
    if snapshot.active_run.player_role == "partner_a":
        collected.extend(snapshot.active_run.answers)
    return collected


def sequential_prefer_answer_bank_events(player_role: PlayerRoleName) -> bool:
    """Default for A-then-B couple play: only the bank-consuming run prefers coverage.

    Simultaneous couple play should set ``LoadedGame.prefer_answer_bank_events``
    explicitly (typically ``False`` while both partners answer live).
    """
    return player_role == "partner_b"


def hydrate_loaded_game(snapshot: GameSnapshot) -> LoadedGame:
    """Build an in-memory ``LoadedGame`` from a RAM ``GameSnapshot``."""
    validate_game_snapshot(snapshot)
    session = session_from_run_snapshot(snapshot.active_run)
    player_role = snapshot.active_run.player_role
    return LoadedGame(
        game_id=snapshot.game_id,
        mode=snapshot.mode,
        session=session,
        answer_bank=AnswerBank.from_recorded_answers(_answers_for_bank(snapshot)),
        partner_a_runs=[copy_run_snapshot(run) for run in snapshot.partner_a_runs],
        player_role=player_role,
        run_number=snapshot.active_run.run_number,
        prefer_answer_bank_events=sequential_prefer_answer_bank_events(player_role),
    )


def export_loaded_game(loaded: LoadedGame) -> GameSnapshot:
    """Rebuild a ``GameSnapshot`` from a ``LoadedGame`` (omit answer snapshots)."""
    return GameSnapshot(
        game_id=loaded.game_id,
        mode=loaded.mode,
        active_run=run_snapshot_from_session(
            loaded.session,
            player_role=loaded.player_role,
            run_number=loaded.run_number,
        ),
        partner_a_runs=[copy_run_snapshot(run) for run in loaded.partner_a_runs],
        config=GameConfig(max_events=loaded.session.config.max_events),
    )


def validate_game_snapshot(snapshot: GameSnapshot) -> None:
    if snapshot.active_run is None:
        raise ValueError("GameSnapshot.active_run is required")
    run = snapshot.active_run
    if run.player_role not in _VALID_PLAYER_ROLES:
        raise ValueError(f"Invalid player_role: {run.player_role!r}")
    status = SessionStatus(run.status)
    if status not in _VALID_RUN_STATUSES:
        raise ValueError(f"Invalid run status: {run.status!r}")
    if not isinstance(run.rng_seed, int):
        raise ValueError("active_run.rng_seed must be an int")


@dataclass
class RunSnapshot:
    run_id: str
    player_role: PlayerRoleName
    run_number: int
    status: SessionStatus
    rng_seed: int
    events_played: int
    events_played_ids: list[str]
    timeline: list[TimelineEntry]
    answers: list[RecordedAnswer]
    event_variables: dict[str, Any]
    current_event_id: str | None
    end_reason: str | None
    max_events: int
    state: SimulationState = field(default_factory=SimulationState)


@dataclass
class GameSnapshot:
    game_id: str
    mode: str
    active_run: RunSnapshot
    partner_a_runs: list[RunSnapshot]
    config: GameConfig


@dataclass
class LoadedGame:
    game_id: str
    mode: str
    session: GameSession
    answer_bank: AnswerBank
    partner_a_runs: list[RunSnapshot]
    player_role: PlayerRoleName
    run_number: int
    prefer_answer_bank_events: bool = False
