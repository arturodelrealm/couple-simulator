"""GameEngine new_session hydrate and snapshot load/export."""

import pytest

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.content.catalog import (
    load_catalog,
    package_events_directory,
)
from couple_simulator_engine.engine import GameEngine
from couple_simulator_engine.enums import PlayerSex, SessionStatus
from couple_simulator_engine.player import Player
from couple_simulator_engine.session import RecordedAnswer
from couple_simulator_engine.snapshot import GameSnapshot, RunSnapshot
from couple_simulator_engine.state import SimulationState


def _engine() -> GameEngine:
    return GameEngine(load_catalog(package_events_directory()))


def _named_player() -> Player:
    return Player(
        id="p-a",
        name="Jordan",
        sex=PlayerSex.MALE,
        game_age=30,
        game_relation_happiness=75,
    )


def test_new_session_places_player_on_partner_a_and_begins_simulation() -> None:
    engine = _engine()
    player = _named_player()
    session = engine.new_session(player, seed=42)
    assert session.state.partner_a is player
    assert session.state.partner_a.name == "Jordan"
    assert session.state.partner_a.simulation_age == player.game_age
    assert session.state.partner_a.simulation_relation_happiness == 75
    assert isinstance(session.rng.seed, int)
    assert session.rng.seed == 42
    assert session.config.max_events == 5


def test_new_session_optional_max_events_overrides_config() -> None:
    engine = GameEngine(
        load_catalog(package_events_directory()), GameConfig(max_events=5)
    )
    session = engine.new_session(_named_player(), max_events=3)
    assert session.config.max_events == 3


def test_load_game_export_snapshot_round_trip() -> None:
    engine = _engine()
    player = _named_player()
    player.begin_simulation()
    player.set_simulation_age(31)
    state = SimulationState(partner_a=player)
    snapshot = GameSnapshot(
        game_id="g1",
        mode="solo",
        active_run=RunSnapshot(
            run_id="r1",
            player_role="partner_a",
            run_number=1,
            status=SessionStatus.ACTIVE,
            rng_seed=99,
            events_played=0,
            events_played_ids=[],
            timeline=[],
            answers=[
                RecordedAnswer(
                    event_id="weekend_trip",
                    question_id="go",
                    option_id="yes",
                )
            ],
            event_variables={},
            current_event_id=None,
            end_reason=None,
            max_events=5,
            state=state,
        ),
        partner_a_runs=[],
        config=GameConfig(max_events=5),
    )
    loaded = engine.load_game(snapshot)
    assert loaded.session.rng.seed == 99
    assert loaded.session.state.partner_a.name == "Jordan"
    assert loaded.answer_bank.has_coverage_for("weekend_trip")
    exported = engine.export_snapshot(loaded)
    assert exported.game_id == "g1"
    assert exported.active_run.rng_seed == 99
    assert exported.active_run.answers[0].option_id == "yes"
    assert exported.active_run.state.partner_a.simulation_age == 31


def test_load_then_select_present_export_keeps_current_event_id() -> None:
    engine = _engine()
    session = engine.new_session(_named_player(), seed=42)
    snapshot = engine.export_snapshot(
        engine.load_game(
            GameSnapshot(
                game_id="g2",
                mode="solo",
                active_run=RunSnapshot(
                    run_id=session.session_id,
                    player_role="partner_a",
                    run_number=1,
                    status=session.status,
                    rng_seed=session.rng.seed,
                    events_played=session.events_played,
                    events_played_ids=list(session.events_played_ids),
                    timeline=list(session.timeline),
                    answers=list(session.answers),
                    event_variables=dict(session.event_variables),
                    current_event_id=None,
                    end_reason=None,
                    max_events=session.config.max_events,
                    state=session.state,
                ),
                partner_a_runs=[],
                config=session.config,
            )
        )
    )
    loaded = engine.load_game(snapshot)
    event = engine.select_next_event(loaded.session)
    assert event is not None
    engine.present_event(event)
    loaded.session.current_event_id = event.id
    exported = engine.export_snapshot(loaded)
    assert exported.active_run.current_event_id == event.id


def test_load_game_rejects_invalid_player_role() -> None:
    engine = _engine()
    snapshot = GameSnapshot(
        game_id="g3",
        mode="solo",
        active_run=RunSnapshot(
            run_id="r-bad",
            player_role="partner_a",
            run_number=1,
            status=SessionStatus.ACTIVE,
            rng_seed=1,
            events_played=0,
            events_played_ids=[],
            timeline=[],
            answers=[],
            event_variables={},
            current_event_id=None,
            end_reason=None,
            max_events=5,
        ),
        partner_a_runs=[],
        config=GameConfig(),
    )
    snapshot.active_run.player_role = "spectator"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="player_role"):
        engine.load_game(snapshot)
