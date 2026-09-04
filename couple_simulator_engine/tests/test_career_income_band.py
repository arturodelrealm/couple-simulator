"""Career events set persistent income_band for the post-event economy tick."""

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.content.catalog import (
    load_catalog,
    package_events_directory,
)
from couple_simulator_engine.content.definitions import (
    EventDefinition,
    OptionDefinition,
    OutcomeDefinition,
    QuestionDefinition,
)
from couple_simulator_engine.enums import PlayerSex
from couple_simulator_engine.player import Player
from couple_simulator_engine.resolution.event_resolver import resolve_event
from couple_simulator_engine.rng import SeededRNG
from couple_simulator_engine.session import Answer, GameSession
from couple_simulator_engine.state import SimulationState


def _session() -> GameSession:
    state = SimulationState()
    state.begin_simulation()
    return GameSession(
        session_id="career-econ",
        player=Player(id="p1", name="Alex", sex=PlayerSex.OTHER),
        state=state,
        config=GameConfig(),
        rng=SeededRNG(1),
    )


def _packaged(event_id: str) -> EventDefinition:
    catalog = load_catalog(package_events_directory())
    event = catalog.get(event_id)
    assert event is not None
    return event


def _zero_effect_event(event_id: str) -> EventDefinition:
    return EventDefinition(
        id=event_id,
        title="Noop",
        description=None,
        tags=(),
        life_stage=None,
        eligibility=None,
        questions=(
            QuestionDefinition(
                id="q1",
                text="Continue",
                options=(OptionDefinition(id="ok", text="OK"),),
            ),
        ),
        outcomes=(OutcomeDefinition(id="ok", when=None, actions=()),),
        default_actions=(),
        mismatch_actions=(),
    )


def _economy_action(resolution) -> dict:
    matches = [
        action.args
        for action in resolution.client_actions
        if action.type == "post_event_economy"
    ]
    assert len(matches) == 1
    return matches[0]


def test_entertaining_job_offers_loads() -> None:
    event = _packaged("entertaining_job_offers")
    assert event.id == "entertaining_job_offers"


def test_calama_sets_high_band_and_next_tick_income_is_eight() -> None:
    session = _session()
    resolve_event(
        session,
        _packaged("entertaining_job_offers"),
        [Answer(question_id="which_offer", option_id="calama_big_salary")],
    )
    assert session.state.tags["income_band"] == "high"
    resolution = resolve_event(
        session,
        _zero_effect_event("after_calama"),
        [Answer(question_id="q1", option_id="ok")],
    )
    economy = _economy_action(resolution)
    assert economy["income"] == 8
    assert economy["income_band"] == "high"


def test_daily_commute_sets_low_band_and_next_tick_income_is_four() -> None:
    session = _session()
    resolve_event(
        session,
        _packaged("entertaining_job_offers"),
        [Answer(question_id="which_offer", option_id="daily_commute")],
    )
    assert session.state.tags["income_band"] == "low"
    resolution = resolve_event(
        session,
        _zero_effect_event("after_commute"),
        [Answer(question_id="q1", option_id="ok")],
    )
    economy = _economy_action(resolution)
    assert economy["income"] == 4
    assert economy["income_band"] == "low"


def test_go_all_in_sets_high_band() -> None:
    session = _session()
    resolve_event(
        session,
        _packaged("adult_content_deal"),
        [Answer(question_id="what_to_do", option_id="go_all_in")],
    )
    assert session.state.tags["income_band"] == "high"


def test_mask_only_sets_mid_band() -> None:
    session = _session()
    resolve_event(
        session,
        _packaged("adult_content_deal"),
        [Answer(question_id="what_to_do", option_id="mask_only")],
    )
    assert session.state.tags["income_band"] == "mid"


def test_decline_does_not_set_income_band() -> None:
    session = _session()
    resolve_event(
        session,
        _packaged("adult_content_deal"),
        [Answer(question_id="what_to_do", option_id="decline_values")],
    )
    assert "income_band" not in session.state.tags


def test_packaged_catalog_still_loads_all_events() -> None:
    catalog = load_catalog(package_events_directory())
    assert catalog.get("entertaining_job_offers") is not None
    assert catalog.get("adult_content_deal") is not None
    assert len(catalog.all_events()) >= 2
