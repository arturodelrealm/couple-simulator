"""Load fixture dummy events and packaged production events."""

from fixture_events import FIXTURE_EVENTS_DIRECTORY

from couple_simulator_engine.content.catalog import (
    load_catalog,
    package_events_directory,
)
from couple_simulator_engine.content.definitions import (
    ActionDefinition,
    TextField,
    TextPresentation,
)


def test_dummy_events_load_from_fixture_directory() -> None:
    catalog = load_catalog(FIXTURE_EVENTS_DIRECTORY)
    events = {event.id: event for event in catalog.all_events()}

    assert set(events) == {
        "weekend_trip",
        "buy_house_light",
        "career_offer",
        "midlife_checkpoint",
        "burnout",
    }


def test_buy_house_light_eligibility_compares_finances() -> None:
    catalog = load_catalog(FIXTURE_EVENTS_DIRECTORY)
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
    catalog = load_catalog(FIXTURE_EVENTS_DIRECTORY)
    event = catalog.get("career_offer")
    assert event is not None
    assert event.questions[0].id == "career_choice"
    paths = [outcome.when["path"] for outcome in event.outcomes if outcome.when]
    assert paths == ["answers/career_choice", "answers/career_choice"]


def test_midlife_checkpoint_advances_life_stage() -> None:
    catalog = load_catalog(FIXTURE_EVENTS_DIRECTORY)
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
    catalog = load_catalog(FIXTURE_EVENTS_DIRECTORY)
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


def _uniform_delta(action: ActionDefinition) -> dict[str, int]:
    delta = action.args["delta"]
    assert isinstance(delta, dict)
    distribution = delta["distribution"]
    assert distribution["kind"] == "uniform"
    params = distribution["params"]
    assert isinstance(params, dict)
    return params


def test_going_bald_is_for_both_players_with_wellness_forks() -> None:
    catalog = load_catalog(package_events_directory())
    event = catalog.get("going_bald")
    assert event is not None
    assert event.use_answer_bank is True
    assert event.player_role is None
    assert event.mismatch_actions
    mismatch_conversation = event.mismatch_actions[0]
    assert mismatch_conversation.type == "add_conversation"
    assert mismatch_conversation.args["speaker"] == "partner_a"
    assert mismatch_conversation.args["text_key"] == (
        "events.going_bald.conversations.mismatch"
    )
    option_ids = {option.id for option in event.questions[0].options}
    assert option_ids == {"let_nature", "buzz_cut", "implant", "hide_it"}
    assert not any(
        action.type == "add_timeline_entry"
        for outcome in event.outcomes
        for action in outcome.actions
    )
    implant = next(outcome for outcome in event.outcomes if outcome.id == "implant")
    implant_stats = {
        action.args["variable"]: _uniform_delta(action)
        for action in implant.actions
        if action.type == "modify_stat"
    }
    assert implant_stats == {
        "wellness": {"min": -7, "max": -3},
        "quality_of_life": {"min": 3, "max": 7},
        "finances": {"min": -7, "max": -3},
    }
    wellness_by_outcome = {
        outcome.id: _uniform_delta(action)
        for outcome in event.outcomes
        for action in outcome.actions
        if action.type == "modify_stat" and action.args["variable"] == "wellness"
    }
    assert wellness_by_outcome == {
        "let_nature": {"min": 10, "max": 14},
        "buzz_cut": {"min": 6, "max": 10},
        "implant": {"min": -7, "max": -3},
        "hide_it": {"min": -10, "max": -6},
    }


def test_friend_who_wont_leave_forks_wellness_and_quality_of_life() -> None:
    catalog = load_catalog(package_events_directory())
    event = catalog.get("friend_who_wont_leave")
    assert event is not None
    assert event.use_answer_bank is True
    option_ids = {option.id for option in event.questions[0].options}
    assert option_ids == {"lock_out", "ask_nicely", "split_rent", "let_stay"}

    def _stats(outcome_id: str) -> dict[str, dict[str, int]]:
        outcome = next(item for item in event.outcomes if item.id == outcome_id)
        return {
            action.args["variable"]: _uniform_delta(action)
            for action in outcome.actions
            if action.type == "modify_stat"
        }

    kick_out = {
        "wellness": {"min": -12, "max": -8},
        "quality_of_life": {"min": 3, "max": 7},
    }
    assert _stats("lock_out") == kick_out
    assert _stats("ask_nicely") == kick_out
    assert _stats("split_rent") == {"quality_of_life": {"min": -7, "max": -3}}
    assert _stats("let_stay") == {
        "wellness": {"min": 8, "max": 12},
        "quality_of_life": {"min": -12, "max": -8},
    }
    for outcome in event.outcomes:
        types = [action.type for action in outcome.actions]
        assert "add_conversation" in types
        assert "add_timeline_entry" in types


def _assert_i18n_text_field(text: TextField) -> None:
    if isinstance(text, str):
        assert text.startswith("events.")
        return
    assert isinstance(text, TextPresentation)
    assert text.default_key.startswith("events.")
    if text.by_role is not None:
        for key in text.by_role.values():
            assert key.startswith("events.")
    if text.by_sex is not None:
        for key in text.by_sex.values():
            assert key.startswith("events.")


def test_packaged_event_copy_fields_are_i18n_keys() -> None:
    catalog = load_catalog(package_events_directory())
    for event in catalog.all_events():
        assert event.title.startswith("events.")
        if event.description is not None:
            assert event.description.startswith("events.")
        for question in event.questions:
            _assert_i18n_text_field(question.text)
            for option in question.options:
                _assert_i18n_text_field(option.text)
        for action in (*event.default_actions, *event.mismatch_actions):
            if action.type == "add_conversation":
                assert "text_key" in action.args
                assert str(action.args["text_key"]).startswith("events.")
                assert "text" not in action.args
            if action.type == "add_timeline_entry":
                assert "title_key" in action.args
                assert str(action.args["title_key"]).startswith("events.")
                assert "title" not in action.args
        for outcome in event.outcomes:
            for action in outcome.actions:
                if action.type == "add_conversation":
                    assert "text_key" in action.args
                    assert str(action.args["text_key"]).startswith("events.")
                    assert "text" not in action.args
                if action.type == "add_timeline_entry":
                    assert "title_key" in action.args
                    assert str(action.args["title_key"]).startswith("events.")
                    assert "title" not in action.args
