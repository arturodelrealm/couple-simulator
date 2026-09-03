from couple_simulator_engine.enums import LifeStage, PlayerSex, RelationshipStatus
from couple_simulator_engine.player import Player
from couple_simulator_engine.state import SimulationState

from app.schemas.simulation import SimulationStateRead
from app.services.simulation_mapper import (
    engine_player_to_dict,
    public_simulation_state,
    simulation_state_from_dict,
    simulation_state_to_dict,
)


def _partner_payload(*, player_id: str, name: str) -> dict:
    return engine_player_to_dict(
        Player(id=player_id, name=name, sex=PlayerSex.OTHER),
    )


def _base_snapshot(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "partner_a": _partner_payload(player_id="a", name="Alex"),
        "partner_b": _partner_payload(player_id="b", name="Blake"),
        "finances": 40,
        "quality_of_life": 55,
        "children": 1,
        "life_stage": LifeStage.ADULT.value,
        "relationship_status": RelationshipStatus.TOGETHER.value,
    }
    payload.update(overrides)
    return payload


def test_simulation_state_read_omits_removed_stats():
    assert "career" not in SimulationStateRead.model_fields
    assert "adventures" not in SimulationStateRead.model_fields


def test_from_dict_ignores_legacy_career_and_adventures():
    snapshot = _base_snapshot(career=80, adventures=25)

    state = simulation_state_from_dict(snapshot)

    assert state.finances == 40
    assert state.quality_of_life == 55
    assert state.children == 1
    assert not hasattr(state, "career")
    assert not hasattr(state, "adventures")


def test_from_dict_uses_engine_defaults_when_couple_stats_missing():
    snapshot = {
        "partner_a": _partner_payload(player_id="a", name="Alex"),
        "partner_b": _partner_payload(player_id="b", name="Blake"),
    }

    state = simulation_state_from_dict(snapshot)
    defaults = SimulationState()

    assert state.finances == defaults.finances
    assert state.quality_of_life == defaults.quality_of_life
    assert state.children == defaults.children
    assert state.life_stage == defaults.life_stage
    assert state.relationship_status == defaults.relationship_status


def test_to_dict_and_public_state_omit_removed_keys():
    snapshot = _base_snapshot(career=90, adventures=10)
    state = simulation_state_from_dict(snapshot)

    persisted = simulation_state_to_dict(state)
    public = public_simulation_state(state)

    assert "career" not in persisted
    assert "adventures" not in persisted
    assert "career" not in public
    assert "adventures" not in public
    SimulationStateRead.model_validate(public)
