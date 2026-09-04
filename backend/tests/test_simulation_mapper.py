from couple_simulator_engine.enums import (
    HousingQuality,
    HousingType,
    LifeStage,
    PlayerSex,
    RelationshipStatus,
)
from couple_simulator_engine.player import Player
from couple_simulator_engine.state import Housing, Mascot, SimulationState

from app.schemas.simulation import SimulationStateRead
from app.services.simulation_mapper import (
    engine_player_from_dict,
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
    assert "wellness" in SimulationStateRead.model_fields
    assert "housing" in SimulationStateRead.model_fields
    assert "mascot" in SimulationStateRead.model_fields
    assert "tags" in SimulationStateRead.model_fields
    assert "partner_a_avatar" in SimulationStateRead.model_fields
    assert "partner_b_avatar" in SimulationStateRead.model_fields


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
    assert state.wellness == defaults.wellness
    assert state.housing == defaults.housing
    assert state.mascot is None
    assert state.tags == {}


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
    assert public["wellness"] == 50
    assert public["housing"] == {
        "place": "Providencia",
        "type": "apartment",
        "quality": "ok",
    }
    assert public["mascot"] is None
    assert public["tags"] == {}
    assert public["partner_a_avatar"] is None
    assert public["partner_b_avatar"] is None


def test_from_dict_legacy_snapshot_without_household_uses_defaults():
    snapshot = _base_snapshot()
    assert "wellness" not in snapshot
    assert "housing" not in snapshot
    assert "mascot" not in snapshot
    assert "tags" not in snapshot

    state = simulation_state_from_dict(snapshot)
    defaults = SimulationState()

    assert state.wellness == 50
    assert state.housing.place == defaults.housing.place
    assert state.housing.type == HousingType.APARTMENT
    assert state.housing.quality == HousingQuality.OK
    assert state.mascot is None
    assert state.tags == {}


def test_to_dict_from_dict_round_trips_non_default_household():
    snapshot = _base_snapshot(
        wellness=12,
        housing={"place": "Las Condes", "type": "house", "quality": "excellent"},
        mascot={"species": "cat", "name": "Michi"},
        tags={"owns_house": True, "job": "engineer"},
    )
    state = simulation_state_from_dict(snapshot)
    persisted = simulation_state_to_dict(state)
    restored = simulation_state_from_dict(persisted)

    assert restored.wellness == 12
    assert restored.housing == Housing(
        place="Las Condes",
        type=HousingType.HOUSE,
        quality=HousingQuality.EXCELLENT,
    )
    assert restored.mascot == Mascot(species="cat", name="Michi")
    assert restored.tags == {"owns_house": True, "job": "engineer"}
    public = public_simulation_state(restored)
    SimulationStateRead.model_validate(public)
    assert public["housing"]["type"] == "house"
    assert public["mascot"] == {"species": "cat", "name": "Michi"}


def test_public_simulation_state_includes_partner_avatars():
    snapshot = _base_snapshot()
    snapshot["partner_a"] = engine_player_to_dict(
        Player(
            id="a",
            name="Alex",
            sex=PlayerSex.OTHER,
            avatar_config={"topVariant": "bob", "facialHairProbability": 100},
        ),
    )
    snapshot["partner_b"] = engine_player_to_dict(
        Player(
            id="b",
            name="Blake",
            sex=PlayerSex.OTHER,
            avatar_config={"topVariant": "shortFlat"},
        ),
    )
    state = simulation_state_from_dict(snapshot)
    public = public_simulation_state(state)

    SimulationStateRead.model_validate(public)
    assert public["partner_a_avatar"] == {
        "topVariant": "bob",
        "facialHairProbability": 100,
    }
    assert public["partner_b_avatar"] == {"topVariant": "shortFlat"}
    persisted = simulation_state_to_dict(state)
    restored = simulation_state_from_dict(persisted)
    assert restored.partner_a.avatar_config == {
        "topVariant": "bob",
        "facialHairProbability": 100,
    }


def test_avatar_probabilities_coerce_json_floats_and_digit_strings():
    player = engine_player_from_dict(
        {
            "id": "a",
            "name": "Alex",
            "sex": PlayerSex.OTHER.value,
            "game_age": 22,
            "game_relation_happiness": 100,
            "simulation_age": 22,
            "simulation_relation_happiness": 100,
            "avatar_config": {
                "topVariant": "bob",
                "facialHairProbability": 0.0,
                "accessoriesProbability": "100",
            },
        }
    )
    assert player.avatar_config == {
        "topVariant": "bob",
        "facialHairProbability": 0,
        "accessoriesProbability": 100,
    }
