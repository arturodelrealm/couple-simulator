"""Evaluation context and ``should_apply`` wrapper (spec §11)."""

from fixture_events import FIXTURE_EVENTS_DIRECTORY

from couple_simulator_engine.conditions import (
    build_evaluation_context,
    evaluation_mode,
    should_apply,
)
from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.content.catalog import load_catalog
from couple_simulator_engine.content.definitions import EventDefinition
from couple_simulator_engine.enums import PlayerSex
from couple_simulator_engine.player import Player
from couple_simulator_engine.rng import SeededRNG
from couple_simulator_engine.session import Answer, GameSession
from couple_simulator_engine.state import SimulationState

_HOUSE_ELIGIBILITY_DOMAIN = {
    "type": "all",
    "items": [
        {
            "type": "compare",
            "path": "state/finances",
            "op": "gte",
            "value": 40,
        },
        {
            "type": "compare",
            "path": "state/age",
            "op": "gte",
            "value": 25,
        },
    ],
}

_SPEC_11_5_CAREER_WHEN = {
    "type": "compare",
    "path": "answers/career_choice",
    "op": "eq",
    "value": "accept",
}


def _session(
    *,
    finances: int = 50,
    age: int = 22,
    event_variables: dict[str, int] | None = None,
) -> GameSession:
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
        event_variables=dict(event_variables or {}),
    )


def _catalog_event(event_id: str) -> EventDefinition:
    catalog = load_catalog(FIXTURE_EVENTS_DIRECTORY)
    event = catalog.get(event_id)
    assert event is not None
    return event


def test_should_apply_none_is_true() -> None:
    ctx = build_evaluation_context(_session(), _catalog_event("career_offer"), [])
    assert should_apply(None, ctx) is True


def test_context_keys_and_player_sex_string() -> None:
    event = _catalog_event("buy_house_light")
    ctx = build_evaluation_context(_session(), event, [])
    assert set(ctx) == {
        "state",
        "event_variables",
        "answers",
        "player",
        "tags",
        "flags",
        "mode",
    }
    assert ctx["mode"] == "solo"
    assert ctx["flags"] == {}
    assert ctx["tags"] == ["financial", "housing"]
    assert ctx["player"] == {"id": "p1", "name": "Alex", "sex": "female"}
    assert isinstance(ctx["player"]["sex"], str)


def test_house_eligibility_domain_pattern_on_built_context() -> None:
    event = _catalog_event("buy_house_light")
    ctx = build_evaluation_context(_session(finances=55, age=30), event, [])
    assert should_apply(_HOUSE_ELIGIBILITY_DOMAIN, ctx) is True
    assert should_apply(event.eligibility, ctx) is True

    too_poor = build_evaluation_context(_session(finances=30, age=30), event, [])
    assert should_apply(event.eligibility, too_poor) is False
    assert should_apply(_HOUSE_ELIGIBILITY_DOMAIN, too_poor) is False


def test_answers_career_choice_compare() -> None:
    event = _catalog_event("career_offer")
    answers = [Answer(question_id="career_choice", option_id="accept")]
    ctx = build_evaluation_context(_session(), event, answers)
    assert ctx["answers"]["career_choice"] == "accept"
    assert should_apply(_SPEC_11_5_CAREER_WHEN, ctx) is True
    accepted = next(outcome for outcome in event.outcomes if outcome.id == "accepted")
    declined = next(outcome for outcome in event.outcomes if outcome.id == "declined")
    assert should_apply(accepted.when, ctx) is True
    assert should_apply(declined.when, ctx) is False


def test_partner_b_session_uses_couple_mode() -> None:
    session = _session()
    session.player = session.state.partner_b
    event = _catalog_event("career_offer")
    ctx = build_evaluation_context(session, event, [])
    assert evaluation_mode(session) == "couple"
    assert ctx["mode"] == "couple"
    assert ctx["flags"] == {}


def test_caller_supplied_flags_reach_rules_evaluator_context() -> None:
    event = _catalog_event("career_offer")
    ctx = build_evaluation_context(
        _session(),
        event,
        [],
        flags={"has_mismatch": True, "answers_match": False},
    )
    assert ctx["flags"]["has_mismatch"] is True
    assert ctx["flags"]["answers_match"] is False
    assert should_apply(
        {
            "type": "compare",
            "path": "flags/has_mismatch",
            "op": "eq",
            "value": True,
        },
        ctx,
    )


def test_event_variables_home_desire_compare() -> None:
    event = _catalog_event("buy_house_light")
    ctx = build_evaluation_context(
        _session(event_variables={"home_desire": 3, "home_budget": 2}),
        event,
        [
            Answer(question_id="want_to_buy", option_id="yes"),
            Answer(question_id="budget_ready", option_id="yes"),
        ],
    )
    desire_rule = {
        "type": "compare",
        "path": "event_variables/home_desire",
        "op": "gte",
        "value": 2,
    }
    assert should_apply(desire_rule, ctx) is True
    purchase = next(outcome for outcome in event.outcomes if outcome.id == "purchase")
    keep_renting = next(
        outcome for outcome in event.outcomes if outcome.id == "keep_renting"
    )
    assert should_apply(purchase.when, ctx) is True
    assert should_apply(keep_renting.when, ctx) is False


def test_simulation_tags_are_readable_from_state_paths() -> None:
    session = _session()
    assert session.state.tags == {}
    session.state.tags["owns_house"] = True
    event = _catalog_event("buy_house_light")
    ctx = build_evaluation_context(session, event, [])
    assert ctx["state"]["tags"] == {"owns_house": True}
    assert ctx["tags"] == ["financial", "housing"]
    present = {
        "type": "compare",
        "path": "state/tags/owns_house",
        "op": "eq",
        "value": True,
    }
    missing = {
        "type": "compare",
        "path": "state/tags/has_mascot",
        "op": "eq",
        "value": True,
    }
    assert should_apply(present, ctx) is True
    assert should_apply(missing, ctx) is False
