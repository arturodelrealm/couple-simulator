"""Load the packaged dummy events from spec §9."""

from couple_simulator_engine.content.catalog import (
    load_catalog,
    package_events_directory,
)


def test_dummy_events_load_from_package_directory() -> None:
    catalog = load_catalog(package_events_directory())
    events = {event.id: event for event in catalog.all_events()}

    assert set(events) == {
        "weekend_trip",
        "buy_house_light",
        "career_offer",
        "midlife_checkpoint",
        "burnout",
    }


def test_buy_house_light_eligibility_compares_finances() -> None:
    catalog = load_catalog(package_events_directory())
    event = catalog.get("buy_house_light")
    assert event is not None
    assert event.eligibility == {
        "type": "compare",
        "path": "state/finances",
        "op": "gte",
        "value": 40,
    }
    outcome_ids = {outcome.id for outcome in event.outcomes}
    assert outcome_ids == {"purchase", "keep_renting"}
    assert event.default_actions
    home_vars = {
        action.args["variable"]
        for question in event.questions
        for option in question.options
        for action in option.actions
        if action.type == "set_event_var"
    }
    assert home_vars == {"home_desire", "home_budget"}


def test_career_offer_outcomes_use_answers_path() -> None:
    catalog = load_catalog(package_events_directory())
    event = catalog.get("career_offer")
    assert event is not None
    assert event.questions[0].id == "career_choice"
    paths = [outcome.when["path"] for outcome in event.outcomes if outcome.when]
    assert paths == ["answers/career_choice", "answers/career_choice"]


def test_midlife_checkpoint_advances_life_stage() -> None:
    catalog = load_catalog(package_events_directory())
    event = catalog.get("midlife_checkpoint")
    assert event is not None
    assert event.eligibility == {
        "type": "compare",
        "path": "state/age",
        "op": "gte",
        "value": 38,
    }
    grow = next(outcome for outcome in event.outcomes if outcome.id == "grow")
    types = [action.type for action in grow.actions]
    assert "advance_life_stage" in types


def test_burnout_end_game_includes_reason() -> None:
    catalog = load_catalog(package_events_directory())
    event = catalog.get("burnout")
    assert event is not None
    end_actions = [
        action
        for outcome in event.outcomes
        for action in outcome.actions
        if action.type == "end_game"
    ]
    assert end_actions
    assert end_actions[0].args.get("reason") == "burnout"
