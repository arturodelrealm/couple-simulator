"""GameSession field coverage for spec §5."""

from dataclasses import fields

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.enums import PlayerSex, SessionStatus
from couple_simulator_engine.player import Player
from couple_simulator_engine.rng import SeededRNG
from couple_simulator_engine.session import GameSession
from couple_simulator_engine.state import SimulationState


def test_game_session_has_spec_fields() -> None:
    names = {item.name for item in fields(GameSession)}
    assert names == {
        "session_id",
        "player",
        "state",
        "config",
        "rng",
        "events_played",
        "events_played_ids",
        "timeline",
        "answers",
        "event_variables",
        "status",
        "end_reason",
        "current_event_id",
    }


def test_game_session_defaults() -> None:
    session = GameSession(
        session_id="s1",
        player=Player(id="p1", name="Alex", sex=PlayerSex.MALE),
        state=SimulationState(),
        config=GameConfig(),
        rng=SeededRNG(1),
    )
    assert session.events_played == 0
    assert session.events_played_ids == []
    assert session.event_variables == {}
    assert session.current_event_id is None
    assert session.status == SessionStatus.ACTIVE
    assert session.end_reason is None
