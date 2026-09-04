"""Unit tests for post-event passive economy (no resolve_event wiring)."""

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.enums import HousingQuality, PlayerSex
from couple_simulator_engine.player import Player
from couple_simulator_engine.resolution.post_event_economy import (
    POST_EVENT_ECONOMY_ACTION,
    apply_post_event_economy,
    children_upkeep,
    compute_net_delta,
    housing_upkeep,
    resolve_income_band,
    resolve_passive_income,
)
from couple_simulator_engine.rng import SeededRNG
from couple_simulator_engine.session import GameSession
from couple_simulator_engine.state import SimulationState


def _session(
    *,
    finances: int = 50,
    children: int = 0,
    housing_quality: HousingQuality = HousingQuality.OK,
    tags: dict[str, object] | None = None,
    config: GameConfig | None = None,
) -> GameSession:
    state = SimulationState()
    state.begin_simulation()
    state.set_stat("finances", finances)
    state.set_stat("children", children)
    state.housing.quality = housing_quality
    if tags is not None:
        state.tags = dict(tags)
    return GameSession(
        session_id="econ-1",
        player=Player(id="p1", name="Alex", sex=PlayerSex.OTHER),
        state=state,
        config=config if config is not None else GameConfig(),
        rng=SeededRNG(1),
    )


def _tick(session: GameSession, *, game_finished: bool = False):
    return apply_post_event_economy(session, game_finished=game_finished)


def test_helpers_resolve_income_and_net() -> None:
    config = GameConfig()
    assert resolve_income_band({}) is None
    assert resolve_income_band({"income_band": "high"}) == "high"
    assert resolve_passive_income(config, None) == 2
    assert resolve_passive_income(config, "low") == 4
    assert resolve_passive_income(config, "mid") == 6
    assert resolve_passive_income(config, "high") == 8
    assert resolve_passive_income(config, "unknown") == 2
    assert children_upkeep(config, 0) == 0
    assert children_upkeep(config, 3) == 2
    assert housing_upkeep(config, HousingQuality.OK) == 0
    assert housing_upkeep(config, HousingQuality.EXCELLENT) == 1
    assert compute_net_delta(8, 2, 1) == 5


def test_default_income_plus_two() -> None:
    session = _session()
    actions = _tick(session)
    assert session.state.finances == 52
    assert len(actions) == 1
    action = actions[0]
    assert action.type == POST_EVENT_ECONOMY_ACTION
    assert action.args == {
        "income": 2,
        "upkeep_children": 0,
        "upkeep_housing": 0,
        "net": 2,
        "income_band": None,
    }


def test_low_band_plus_four() -> None:
    session = _session(tags={"income_band": "low"})
    actions = _tick(session)
    assert session.state.finances == 54
    assert actions[0].args["income"] == 4
    assert actions[0].args["income_band"] == "low"
    assert actions[0].args["net"] == 4


def test_mid_band_plus_six() -> None:
    session = _session(tags={"income_band": "mid"})
    actions = _tick(session)
    assert session.state.finances == 56
    assert actions[0].args["income"] == 6
    assert actions[0].args["net"] == 6


def test_high_band_plus_eight() -> None:
    session = _session(tags={"income_band": "high"})
    actions = _tick(session)
    assert session.state.finances == 58
    assert actions[0].args["income"] == 8
    assert actions[0].args["net"] == 8


def test_child_upkeep_once_not_per_child() -> None:
    session = _session(children=3)
    actions = _tick(session)
    assert session.state.finances == 50
    assert actions[0].args["upkeep_children"] == 2
    assert actions[0].args["net"] == 0


def test_excellent_housing_upkeep() -> None:
    session = _session(housing_quality=HousingQuality.EXCELLENT)
    actions = _tick(session)
    assert session.state.finances == 51
    assert actions[0].args["upkeep_housing"] == 1
    assert actions[0].args["net"] == 1


def test_stacked_upkeep() -> None:
    session = _session(
        tags={"income_band": "high"},
        children=1,
        housing_quality=HousingQuality.EXCELLENT,
    )
    actions = _tick(session)
    assert session.state.finances == 55
    assert actions[0].args == {
        "income": 8,
        "upkeep_children": 2,
        "upkeep_housing": 1,
        "net": 5,
        "income_band": "high",
    }


def test_unknown_band_uses_default() -> None:
    session = _session(tags={"income_band": "top"})
    actions = _tick(session)
    assert session.state.finances == 52
    assert actions[0].args["income"] == 2
    assert actions[0].args["income_band"] == "top"


def test_disabled_config_skips_without_mutation() -> None:
    session = _session(config=GameConfig(passive_income_enabled=False))
    actions = _tick(session)
    assert actions == []
    assert session.state.finances == 50


def test_game_finished_skips_without_mutation() -> None:
    session = _session()
    actions = _tick(session, game_finished=True)
    assert actions == []
    assert session.state.finances == 50


def test_net_negative_clamps_finances_to_zero() -> None:
    session = _session(
        finances=1,
        children=1,
        housing_quality=HousingQuality.EXCELLENT,
        config=GameConfig(passive_income_default=0),
    )
    actions = _tick(session)
    assert session.state.finances == 0
    assert actions[0].args["net"] == -3
