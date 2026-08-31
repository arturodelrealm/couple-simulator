"""V0 action registry and handlers (spec §8)."""

import pytest

from couple_simulator_engine.actions.registry import apply_action
from couple_simulator_engine.actions.types import UnknownActionTypeError
from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.content.definitions import ActionDefinition
from couple_simulator_engine.enums import LifeStage, PlayerSex, SessionStatus
from couple_simulator_engine.player import Player
from couple_simulator_engine.rng import SeededRNG
from couple_simulator_engine.session import GameSession
from couple_simulator_engine.state import SimulationState


def _session(*, finances: int = 50, age: int = 22) -> GameSession:
    state = SimulationState()
    state.begin_simulation()
    state.set_stat("finances", finances)
    state.partner_a.set_simulation_age(age)
    state.partner_b.set_simulation_age(age)
    return GameSession(
        session_id="s1",
        player=Player(id="p1", name="Alex", sex=PlayerSex.FEMALE),
        state=state,
        config=GameConfig(),
        rng=SeededRNG(1),
    )


def _ctx(session: GameSession) -> dict[str, object]:
    return {
        "state": session.state.to_dict(),
        "event_variables": session.event_variables,
        "answers": {},
        "player": {
            "id": session.player.id,
            "name": session.player.name,
            "sex": session.player.sex.value,
        },
        "tags": [],
        "flags": {},
        "mode": "solo",
    }


def test_unknown_action_type_raises() -> None:
    session = _session()
    action = ActionDefinition(type="not_a_real_action", args={})
    with pytest.raises(UnknownActionTypeError, match="not_a_real_action"):
        apply_action(action, _ctx(session), session, session.rng)


def test_modify_stat_fixed_delta_updates_state_and_emits_mirror() -> None:
    session = _session()
    action = ActionDefinition(
        type="modify_stat",
        args={"variable": "finances", "delta": 15},
    )
    result = apply_action(action, _ctx(session), session, session.rng)
    assert session.state.finances == 65
    assert len(result) == 1
    assert result[0].type == "modify_stat"
    assert result[0].args == {
        "variable": "finances",
        "delta": 15,
        "new_value": 65,
    }


def test_modify_stat_normal_distribution_uses_rng_and_clamps() -> None:
    session = _session()
    session.state.set_stat("quality_of_life", 98)
    action = ActionDefinition(
        type="modify_stat",
        args={
            "variable": "quality_of_life",
            "delta": {
                "distribution": {
                    "kind": "normal",
                    "params": {"median": 10, "std": 2},
                }
            },
        },
    )
    rng_a = SeededRNG(7)
    rng_b = SeededRNG(7)
    sampled = rng_b.normal(10, 2)
    result = apply_action(action, _ctx(session), session, rng_a)
    expected_new = min(100, 98 + sampled)
    actual_delta = expected_new - 98
    assert session.state.quality_of_life == expected_new
    assert result[0].args["delta"] == actual_delta
    assert result[0].args["new_value"] == expected_new


def test_modify_stat_age_updates_partner_simulation_ages() -> None:
    session = _session(age=22)
    action = ActionDefinition(
        type="modify_stat",
        args={"variable": "age", "delta": 5},
    )
    result = apply_action(action, _ctx(session), session, session.rng)
    assert session.state.partner_a.simulation_age == 27
    assert session.state.partner_b.simulation_age == 27
    assert session.state.age == 27
    assert result[0].args == {"variable": "age", "delta": 5, "new_value": 27}


def test_modify_stat_compatibility_updates_partner_happiness() -> None:
    session = _session()
    action = ActionDefinition(
        type="modify_stat",
        args={"variable": "compatibility", "delta": -10},
    )
    result = apply_action(action, _ctx(session), session, session.rng)
    assert session.state.partner_a.simulation_relation_happiness == 90
    assert session.state.partner_b.simulation_relation_happiness == 90
    assert session.state.compatibility == 90
    assert result[0].args["new_value"] == 90
    assert result[0].args["delta"] == -10


def test_set_event_var_mutates_session_only() -> None:
    session = _session()
    finances = session.state.finances
    action = ActionDefinition(
        type="set_event_var",
        args={"variable": "home_desire", "value": 3},
    )
    result = apply_action(action, _ctx(session), session, session.rng)
    assert result == []
    assert session.event_variables == {"home_desire": 3}
    assert session.state.finances == finances
    assert session.timeline == []
    assert session.status == SessionStatus.ACTIVE


def test_add_conversation_does_not_mutate_state() -> None:
    session = _session()
    snapshot = session.state.to_dict()
    action = ActionDefinition(
        type="add_conversation",
        args={
            "speaker": "partner_a",
            "text": "Hello, {{player.name}}",
            "params": {"name": "{{player.name}}"},
        },
    )
    result = apply_action(action, _ctx(session), session, session.rng)
    assert session.state.to_dict() == snapshot
    assert session.event_variables == {}
    assert len(result) == 1
    assert result[0].type == "add_conversation"
    assert result[0].args["speaker"] == "partner_a"
    assert result[0].args["text"] == "Hello, Alex"
    assert result[0].args["params"] == {"name": "Alex"}


def test_add_conversation_passthrough_text_key() -> None:
    session = _session()
    action = ActionDefinition(
        type="add_conversation",
        args={
            "speaker": "partner_a",
            "text_key": "events.cafe.greeting",
            "params": {"name": "{{player.name}}"},
        },
    )
    result = apply_action(action, _ctx(session), session, session.rng)
    assert result[0].args["text_key"] == "events.cafe.greeting"
    assert "text" not in result[0].args
    assert result[0].args["params"]["name"] == "Alex"


def test_add_timeline_entry_appends_with_state_age() -> None:
    session = _session(age=30)
    action = ActionDefinition(
        type="add_timeline_entry",
        args={"title": "Weekend together", "category": "leisure"},
    )
    result = apply_action(action, _ctx(session), session, session.rng)
    assert len(session.timeline) == 1
    assert session.timeline[0].title == "Weekend together"
    assert session.timeline[0].age == 30
    assert result[0].type == "add_timeline_entry"
    assert result[0].args["age"] == 30
    assert result[0].args["title"] == "Weekend together"
    assert result[0].args["category"] == "leisure"


def test_advance_life_stage_emits_from_to() -> None:
    session = _session()
    assert session.state.life_stage == LifeStage.YOUTH
    action = ActionDefinition(type="advance_life_stage", args={"to": "adult"})
    result = apply_action(action, _ctx(session), session, session.rng)
    assert session.state.life_stage == LifeStage.ADULT
    assert result[0].type == "advance_life_stage"
    assert result[0].args == {"from": "youth", "to": "adult"}


def test_end_game_sets_finished_and_emits_reason() -> None:
    session = _session()
    action = ActionDefinition(type="end_game", args={"reason": "burnout"})
    result = apply_action(action, _ctx(session), session, session.rng)
    assert session.status == SessionStatus.FINISHED
    assert session.end_reason == "burnout"
    assert result[0].type == "end_game"
    assert result[0].args == {"reason": "burnout"}
