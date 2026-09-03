"""Tests for SimulationState defaults, derived couple stats, and clamp rules."""

import pytest

from couple_simulator_engine.clamp import clamp_stat
from couple_simulator_engine.enums import (
    HousingQuality,
    HousingType,
    LifeStage,
    PlayerSex,
    RelationshipStatus,
)
from couple_simulator_engine.player import Player
from couple_simulator_engine.snapshot import copy_simulation_state
from couple_simulator_engine.state import Housing, Mascot, SimulationState


def test_default_initial_values() -> None:
    state = SimulationState()
    assert state.age == 22
    assert state.compatibility == 100
    assert state.finances == 50
    assert state.quality_of_life == 50
    assert state.children == 0
    assert state.wellness == 50
    assert state.mascot is None
    assert state.tags == {}
    assert state.housing.place == "Providencia"
    assert state.housing.type == HousingType.APARTMENT
    assert state.housing.quality == HousingQuality.OK
    assert state.life_stage == LifeStage.YOUTH
    assert state.relationship_status == RelationshipStatus.TOGETHER
    assert state.partner_a.game_age == 22
    assert state.partner_b.game_age == 22
    assert state.partner_a.game_relation_happiness == 100
    assert state.partner_b.game_relation_happiness == 100


def test_age_is_min_of_partner_simulation_ages() -> None:
    state = SimulationState()
    state.partner_a.set_simulation_age(30)
    state.partner_b.set_simulation_age(25)
    assert state.age == 25
    assert state.partner_a.simulation_age == 30
    assert state.partner_b.simulation_age == 25


def test_compatibility_is_min_of_partner_simulation_happiness() -> None:
    state = SimulationState()
    state.partner_a.set_simulation_relation_happiness(80)
    state.partner_b.set_simulation_relation_happiness(40)
    assert state.compatibility == 40


def test_begin_simulation_resets_from_game_stats() -> None:
    state = SimulationState()
    state.partner_a.game_age = 28
    state.partner_a.game_relation_happiness = 70
    state.partner_b.game_age = 26
    state.partner_b.game_relation_happiness = 90
    state.partner_a.set_simulation_age(40)
    state.partner_a.set_simulation_relation_happiness(10)
    state.partner_b.set_simulation_age(50)
    state.partner_b.set_simulation_relation_happiness(20)

    state.begin_simulation()

    assert state.partner_a.game_age == 28
    assert state.partner_a.game_relation_happiness == 70
    assert state.partner_a.simulation_age == 28
    assert state.partner_a.simulation_relation_happiness == 70
    assert state.partner_b.simulation_age == 26
    assert state.partner_b.simulation_relation_happiness == 90
    assert state.age == 26
    assert state.compatibility == 70


def test_clamp_finances_high() -> None:
    assert clamp_stat("finances", 150) == 100


def test_clamp_finances_low() -> None:
    assert clamp_stat("finances", -10) == 0


def test_clamp_children_min() -> None:
    assert clamp_stat("children", -3) == 0
    assert clamp_stat("children", 2) == 2


def test_clamp_age_min() -> None:
    assert clamp_stat("age", 10) == 18
    assert clamp_stat("age", 40) == 40


def test_to_dict_aligns_with_rules_evaluator_paths() -> None:
    state = SimulationState()
    payload = state.to_dict()
    assert payload["finances"] == 50
    assert payload["quality_of_life"] == 50
    assert payload["wellness"] == 50
    assert payload["housing"] == {
        "place": "Providencia",
        "type": "apartment",
        "quality": "ok",
    }
    assert payload["mascot"] is None
    assert payload["tags"] == {}
    assert "adventures" not in payload
    assert "career" not in payload
    assert payload["compatibility"] == 100
    assert payload["age"] == 22
    assert payload["life_stage"] == "youth"
    assert payload["relationship_status"] == "together"
    context = {"state": payload}
    assert context["state"]["finances"] == 50


def test_player_fields() -> None:
    player = Player(id="p1", name="Alex", sex=PlayerSex.OTHER)
    assert player.avatar_config is None
    assert player.sex == PlayerSex.OTHER
    assert player.game_age == 22
    assert player.simulation_age == 22
    assert player.game_relation_happiness == 100
    assert player.simulation_relation_happiness == 100


def test_set_stat_rejects_derived_age_and_compatibility() -> None:
    state = SimulationState()
    with pytest.raises(ValueError, match="derived from players"):
        state.set_stat("age", 30)
    with pytest.raises(ValueError, match="derived from players"):
        state.set_stat("compatibility", 50)


def test_clamp_unknown_stat() -> None:
    with pytest.raises(ValueError, match="Unknown stat"):
        clamp_stat("not_a_stat", 1)


def test_removed_stats_are_unknown() -> None:
    state = SimulationState()
    for variable in ("career", "adventures"):
        with pytest.raises(ValueError, match="Unknown stat"):
            clamp_stat(variable, 50)
        with pytest.raises(ValueError, match="Unknown stat"):
            state.set_stat(variable, 50)


def test_set_stat_clamps_wellness() -> None:
    state = SimulationState()
    assert state.set_stat("wellness", 150) == 100
    assert state.wellness == 100
    assert state.set_stat("wellness", -20) == 0
    assert state.wellness == 0


def test_copy_simulation_state_round_trips_household_fields() -> None:
    original = SimulationState(
        wellness=12,
        housing=Housing(
            place="Las Condes",
            type=HousingType.HOUSE,
            quality=HousingQuality.EXCELLENT,
        ),
        mascot=Mascot(species="cat", name="Michi"),
        tags={"owns_house": True},
    )
    copied = copy_simulation_state(original)
    assert copied.wellness == 12
    assert copied.housing.place == "Las Condes"
    assert copied.housing.type == HousingType.HOUSE
    assert copied.housing.quality == HousingQuality.EXCELLENT
    assert copied.mascot is not None
    assert copied.mascot.species == "cat"
    assert copied.mascot.name == "Michi"
    assert copied.tags == {"owns_house": True}
    copied.housing.place = "Ñuñoa"
    copied.mascot.name = "Other"
    copied.wellness = 99
    copied.tags["owns_house"] = False
    copied.tags["extra"] = 1
    assert original.housing.place == "Las Condes"
    assert original.mascot is not None
    assert original.mascot.name == "Michi"
    assert original.wellness == 12
    assert original.tags == {"owns_house": True}
