"""Event resolution pipeline (spec §6.4, P2)."""

from unittest.mock import MagicMock

import pytest
from fixture_events import FIXTURE_EVENTS_DIRECTORY

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.content.catalog import load_catalog
from couple_simulator_engine.content.definitions import (
    ActionDefinition,
    EventDefinition,
    OptionDefinition,
    OutcomeDefinition,
    QuestionDefinition,
)
from couple_simulator_engine.enums import PlayerSex, SessionStatus
from couple_simulator_engine.player import Player
from couple_simulator_engine.resolution.event_resolver import (
    AnswerValidationError,
    resolve_event,
)
from couple_simulator_engine.rng import SeededRNG
from couple_simulator_engine.session import Answer, GameSession
from couple_simulator_engine.state import SimulationState


def _session(
    *,
    finances: int = 50,
    age: int = 22,
    event_variables: dict[str, int] | None = None,
    current_event_id: str | None = None,
    config: GameConfig | None = None,
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
        config=config or GameConfig(passive_income_enabled=False),
        rng=SeededRNG(1),
        event_variables=dict(event_variables or {}),
        current_event_id=current_event_id,
    )


def _catalog_event(event_id: str) -> EventDefinition:
    catalog = load_catalog(FIXTURE_EVENTS_DIRECTORY)
    event = catalog.get(event_id)
    assert event is not None
    return event


def test_missing_required_answer_raises() -> None:
    event = _catalog_event("buy_house_light")
    session = _session()
    with pytest.raises(AnswerValidationError, match="want_to_buy"):
        resolve_event(
            session,
            event,
            [Answer(question_id="budget_ready", option_id="yes")],
        )


def test_buy_house_light_purchase_path() -> None:
    event = _catalog_event("buy_house_light")
    session = _session(finances=50)
    resolution = resolve_event(
        session,
        event,
        [
            Answer(question_id="want_to_buy", option_id="yes"),
            Answer(question_id="budget_ready", option_id="yes"),
        ],
    )
    assert resolution.applied_outcome_ids == ["purchase"]
    assert session.state.finances == 35
    assert session.state.quality_of_life == 30
    assert any(
        action.type == "modify_stat" and action.args.get("variable") == "finances"
        for action in resolution.client_actions
    )
    assert session.events_played == 1
    assert session.events_played_ids == ["buy_house_light"]
    assert len(session.answers) == 2


def test_career_offer_accept_applies_accepted_only() -> None:
    event = _catalog_event("career_offer")
    session = _session()
    resolution = resolve_event(
        session,
        event,
        [Answer(question_id="career_choice", option_id="accept")],
    )
    assert resolution.applied_outcome_ids == ["accepted"]
    assert session.state.quality_of_life == 35


def test_two_outcomes_both_apply_when_when_is_true() -> None:
    event = EventDefinition(
        id="dual_outcomes",
        title="Dual",
        description=None,
        tags=(),
        life_stage=None,
        eligibility=None,
        questions=(
            QuestionDefinition(
                id="q1",
                text="Choose",
                options=(OptionDefinition(id="a", text="A"),),
            ),
        ),
        outcomes=(
            OutcomeDefinition(
                id="one",
                when=None,
                actions=(
                    ActionDefinition(
                        type="modify_stat",
                        args={"variable": "finances", "delta": 1},
                    ),
                ),
            ),
            OutcomeDefinition(
                id="two",
                when=None,
                actions=(
                    ActionDefinition(
                        type="modify_stat",
                        args={"variable": "quality_of_life", "delta": 2},
                    ),
                ),
            ),
        ),
        default_actions=(),
        mismatch_actions=(),
    )
    session = _session()
    resolution = resolve_event(
        session, event, [Answer(question_id="q1", option_id="a")]
    )
    assert resolution.applied_outcome_ids == ["one", "two"]
    assert session.state.finances == 51
    assert session.state.quality_of_life == 22


def test_default_actions_when_no_outcome_matches() -> None:
    event = _catalog_event("buy_house_light")
    session = _session()
    resolution = resolve_event(
        session,
        event,
        [
            Answer(question_id="want_to_buy", option_id="yes"),
            Answer(question_id="budget_ready", option_id="no"),
        ],
    )
    assert resolution.applied_outcome_ids == []
    assert session.state.finances == 50
    assert any(
        action.type == "add_conversation"
        and action.args.get("text_key")
        == "events.buy_house_light.conversations.leave_open"
        for action in resolution.client_actions
    )


def test_event_variables_cleared_after_resolution() -> None:
    event = _catalog_event("buy_house_light")
    session = _session(
        event_variables={"stale": 1},
        current_event_id="buy_house_light",
    )
    resolve_event(
        session,
        event,
        [
            Answer(question_id="want_to_buy", option_id="yes"),
            Answer(question_id="budget_ready", option_id="yes"),
        ],
    )
    assert session.event_variables == {}
    assert session.current_event_id is None


def test_end_game_action_sets_game_finished() -> None:
    event = _catalog_event("burnout")
    session = _session()
    resolution = resolve_event(
        session,
        event,
        [Answer(question_id="burnout_choice", option_id="quit_job")],
    )
    assert resolution.game_finished is True
    assert session.status == SessionStatus.FINISHED
    assert session.end_reason == "burnout"
    assert any(action.type == "end_game" for action in resolution.client_actions)


def _partner_b_session(*, happiness: int = 70) -> GameSession:
    partner_a = Player(id="p-a", name="Alex", sex=PlayerSex.FEMALE)
    partner_b = Player(id="p-b", name="Sam", sex=PlayerSex.MALE)
    state = SimulationState(partner_a=partner_a, partner_b=partner_b)
    state.begin_simulation()
    partner_a.set_simulation_relation_happiness(happiness)
    partner_b.set_simulation_relation_happiness(happiness)
    return GameSession(
        session_id="s-b",
        player=partner_b,
        state=state,
        config=GameConfig(passive_income_enabled=False),
        rng=SeededRNG(1),
    )


def _choice_event(
    *,
    mismatch_actions: tuple[ActionDefinition, ...] = (),
    outcomes: tuple[OutcomeDefinition, ...] = (),
    default_actions: tuple[ActionDefinition, ...] = (),
    use_answer_bank: bool = True,
    apply_couple_deltas: bool = True,
) -> EventDefinition:
    return EventDefinition(
        id="duo_choice",
        title="Duo",
        description=None,
        tags=(),
        life_stage=None,
        eligibility=None,
        questions=(
            QuestionDefinition(
                id="q1",
                text="Choose",
                options=(
                    OptionDefinition(
                        id="opt_a",
                        text="A",
                        actions=(
                            ActionDefinition(
                                type="modify_stat",
                                args={"variable": "finances", "delta": 1},
                            ),
                        ),
                    ),
                    OptionDefinition(
                        id="opt_b",
                        text="B",
                        actions=(
                            ActionDefinition(
                                type="modify_stat",
                                args={"variable": "finances", "delta": 20},
                            ),
                        ),
                    ),
                ),
            ),
        ),
        outcomes=outcomes,
        default_actions=default_actions,
        mismatch_actions=mismatch_actions,
        use_answer_bank=use_answer_bank,
        apply_couple_deltas=apply_couple_deltas,
    )


def test_partner_b_matching_bank_applies_match_bonus_not_personal() -> None:
    event = _choice_event()
    session = _partner_b_session()
    resolution = resolve_event(
        session,
        event,
        [Answer(question_id="q1", option_id="opt_b")],
        partner_a_answers=[Answer(question_id="q1", option_id="opt_b")],
    )
    assert session.state.partner_a.simulation_relation_happiness == 75
    assert session.state.partner_b.simulation_relation_happiness == 75
    assert session.state.finances == 35
    assert session.answers[0].option_id == "opt_b"
    assert any(
        action.type == "modify_stat"
        and action.args.get("variable") == "compatibility"
        and action.args.get("delta") == 5
        for action in resolution.client_actions
    )


def test_use_answer_bank_false_ignores_partner_a_answers() -> None:
    event = _choice_event(use_answer_bank=False)
    session = _partner_b_session()
    resolve_event(
        session,
        event,
        [Answer(question_id="q1", option_id="opt_b")],
        partner_a_answers=[Answer(question_id="q1", option_id="opt_a")],
    )
    assert session.state.finances == 35
    assert session.state.partner_a.simulation_relation_happiness == 70
    assert session.state.partner_b.simulation_relation_happiness == 70


def test_partner_b_disagreeing_bank_uses_winner_option_and_penalties() -> None:
    event = _choice_event()
    session = _partner_b_session()
    session.rng = MagicMock()
    session.rng.weighted_choice.return_value = "opt_a"
    resolve_event(
        session,
        event,
        [Answer(question_id="q1", option_id="opt_b")],
        partner_a_answers=[Answer(question_id="q1", option_id="opt_a")],
    )
    assert session.state.finances == 16
    assert session.state.partner_a.simulation_relation_happiness == 62
    assert session.state.partner_b.simulation_relation_happiness == 58
    assert session.answers[0].option_id == "opt_b"


def test_partner_b_no_bank_skips_couple_and_personal_deltas() -> None:
    event = _choice_event()
    session = _partner_b_session()
    resolve_event(
        session,
        event,
        [Answer(question_id="q1", option_id="opt_b")],
        partner_a_answers=None,
    )
    assert session.state.finances == 35
    assert session.state.partner_a.simulation_relation_happiness == 70
    assert session.state.partner_b.simulation_relation_happiness == 70


def test_partner_a_ignores_bank_and_couple_deltas() -> None:
    event = _choice_event()
    session = _session()
    resolve_event(
        session,
        event,
        [Answer(question_id="q1", option_id="opt_b")],
        partner_a_answers=[Answer(question_id="q1", option_id="opt_a")],
    )
    assert session.state.finances == 70
    assert session.state.partner_a.simulation_relation_happiness == 100
    assert session.state.partner_b.simulation_relation_happiness == 100


def test_mismatch_actions_run_when_partners_disagree() -> None:
    event = _choice_event(
        mismatch_actions=(
            ActionDefinition(
                type="modify_stat",
                args={"variable": "quality_of_life", "delta": 7},
            ),
        )
    )
    session = _partner_b_session()
    session.rng = MagicMock()
    session.rng.weighted_choice.return_value = "opt_b"
    resolve_event(
        session,
        event,
        [Answer(question_id="q1", option_id="opt_b")],
        partner_a_answers=[Answer(question_id="q1", option_id="opt_a")],
    )
    assert session.state.quality_of_life == 27
    assert session.state.finances == 35


def test_partner_b_incomplete_bank_is_solo() -> None:
    event = _choice_event()
    session = _partner_b_session()
    resolve_event(
        session,
        event,
        [Answer(question_id="q1", option_id="opt_b")],
        partner_a_answers=[],
    )
    assert session.state.finances == 35
    assert session.state.partner_a.simulation_relation_happiness == 70


def test_outcomes_use_effective_option_not_discarded() -> None:
    event = _choice_event(
        outcomes=(
            OutcomeDefinition(
                id="a_won",
                when={
                    "type": "compare",
                    "path": "answers/q1",
                    "op": "eq",
                    "value": "opt_a",
                },
                actions=(),
            ),
            OutcomeDefinition(
                id="b_won",
                when={
                    "type": "compare",
                    "path": "answers/q1",
                    "op": "eq",
                    "value": "opt_b",
                },
                actions=(),
            ),
        )
    )
    session = _partner_b_session()
    session.rng = MagicMock()
    session.rng.weighted_choice.return_value = "opt_a"
    resolution = resolve_event(
        session,
        event,
        [Answer(question_id="q1", option_id="opt_b")],
        partner_a_answers=[Answer(question_id="q1", option_id="opt_a")],
    )
    assert resolution.applied_outcome_ids == ["a_won"]


def test_resolution_passthrough_conversation_and_timeline_keys() -> None:
    event = EventDefinition(
        id="keyed_copy",
        title="events.keyed_copy.title",
        description=None,
        tags=(),
        life_stage=None,
        eligibility=None,
        questions=(
            QuestionDefinition(
                id="q1",
                text="events.keyed_copy.questions.q1",
                options=(OptionDefinition(id="a", text="events.keyed_copy.options.a"),),
            ),
        ),
        outcomes=(
            OutcomeDefinition(
                id="done",
                when=None,
                actions=(
                    ActionDefinition(
                        type="add_conversation",
                        args={
                            "speaker": "narrator",
                            "text_key": "events.keyed_copy.conversations.done",
                        },
                    ),
                    ActionDefinition(
                        type="add_timeline_entry",
                        args={
                            "title_key": "events.keyed_copy.timeline.done",
                            "description_key": (
                                "events.keyed_copy.timeline.done_description"
                            ),
                            "category": "life",
                        },
                    ),
                ),
            ),
        ),
        default_actions=(),
        mismatch_actions=(),
    )
    session = _session()
    resolution = resolve_event(
        session, event, [Answer(question_id="q1", option_id="a")]
    )
    conversation = next(
        action
        for action in resolution.client_actions
        if action.type == "add_conversation"
    )
    timeline = next(
        action
        for action in resolution.client_actions
        if action.type == "add_timeline_entry"
    )
    assert conversation.args["text_key"] == "events.keyed_copy.conversations.done"
    assert "text" not in conversation.args
    assert timeline.args["title_key"] == "events.keyed_copy.timeline.done"
    assert (
        timeline.args["description_key"]
        == "events.keyed_copy.timeline.done_description"
    )
    assert timeline.args["title"] == "events.keyed_copy.timeline.done"
    assert session.timeline[0].title == "events.keyed_copy.timeline.done"


def test_mismatch_actions_skipped_when_answers_match() -> None:
    event = _choice_event(
        mismatch_actions=(
            ActionDefinition(
                type="modify_stat",
                args={"variable": "quality_of_life", "delta": 7},
            ),
        )
    )
    session = _partner_b_session()
    resolve_event(
        session,
        event,
        [Answer(question_id="q1", option_id="opt_a")],
        partner_a_answers=[Answer(question_id="q1", option_id="opt_a")],
    )
    assert session.state.quality_of_life == 20
    assert session.state.finances == 16


def test_couple_flags_include_per_question_match_count() -> None:
    event = EventDefinition(
        id="quiz",
        title="Quiz",
        description=None,
        tags=(),
        life_stage=None,
        eligibility=None,
        questions=(
            QuestionDefinition(
                id="q1",
                text="Q1",
                options=(
                    OptionDefinition(id="opt_a", text="A"),
                    OptionDefinition(id="opt_b", text="B"),
                ),
            ),
            QuestionDefinition(
                id="q2",
                text="Q2",
                options=(
                    OptionDefinition(id="opt_a", text="A"),
                    OptionDefinition(id="opt_b", text="B"),
                ),
            ),
        ),
        outcomes=(
            OutcomeDefinition(
                id="one_hit",
                when={
                    "type": "compare",
                    "path": "flags/match_count",
                    "op": "eq",
                    "value": 1,
                },
                actions=(
                    ActionDefinition(
                        type="set_event_var",
                        args={"variable": "hits", "value": 1},
                    ),
                ),
            ),
        ),
        default_actions=(),
        mismatch_actions=(),
    )
    session = _partner_b_session()
    resolution = resolve_event(
        session,
        event,
        [
            Answer(question_id="q1", option_id="opt_a"),
            Answer(question_id="q2", option_id="opt_b"),
        ],
        partner_a_answers=[
            Answer(question_id="q1", option_id="opt_a"),
            Answer(question_id="q2", option_id="opt_a"),
        ],
    )
    assert resolution.applied_outcome_ids == ["one_hit"]
    assert session.event_variables == {}


def test_apply_couple_deltas_false_skips_penalties_but_keeps_match_flags() -> None:
    event = _choice_event(apply_couple_deltas=False)
    session = _partner_b_session()
    session.rng = MagicMock()
    session.rng.weighted_choice.return_value = "opt_a"
    resolve_event(
        session,
        event,
        [Answer(question_id="q1", option_id="opt_b")],
        partner_a_answers=[Answer(question_id="q1", option_id="opt_a")],
    )
    assert session.state.finances == 35
    assert session.state.partner_a.simulation_relation_happiness == 70
    assert session.state.partner_b.simulation_relation_happiness == 70
    assert session.state.mismatches == 0


def test_apply_couple_deltas_false_skips_mismatch_actions() -> None:
    event = _choice_event(
        apply_couple_deltas=False,
        mismatch_actions=(
            ActionDefinition(
                type="modify_stat",
                args={"variable": "quality_of_life", "delta": 7},
            ),
        ),
    )
    session = _partner_b_session()
    resolve_event(
        session,
        event,
        [Answer(question_id="q1", option_id="opt_b")],
        partner_a_answers=[Answer(question_id="q1", option_id="opt_a")],
    )
    assert session.state.quality_of_life == 20


def test_mismatches_increment_per_disagreeing_question() -> None:
    event = EventDefinition(
        id="quiz",
        title="Quiz",
        description=None,
        tags=(),
        life_stage=None,
        eligibility=None,
        questions=(
            QuestionDefinition(
                id="q1",
                text="Q1",
                options=(
                    OptionDefinition(id="opt_a", text="A"),
                    OptionDefinition(id="opt_b", text="B"),
                ),
            ),
            QuestionDefinition(
                id="q2",
                text="Q2",
                options=(
                    OptionDefinition(id="opt_a", text="A"),
                    OptionDefinition(id="opt_b", text="B"),
                ),
            ),
        ),
        outcomes=(),
        default_actions=(),
        mismatch_actions=(),
    )
    session = _partner_b_session()
    session.rng = MagicMock()
    session.rng.weighted_choice.side_effect = ["opt_a", "opt_b"]
    resolve_event(
        session,
        event,
        [
            Answer(question_id="q1", option_id="opt_b"),
            Answer(question_id="q2", option_id="opt_b"),
        ],
        partner_a_answers=[
            Answer(question_id="q1", option_id="opt_a"),
            Answer(question_id="q2", option_id="opt_a"),
        ],
    )
    assert session.state.mismatches == 2


def _zero_effect_event(event_id: str = "noop_tick") -> EventDefinition:
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


def test_resolve_applies_default_passive_income() -> None:
    session = _session(config=GameConfig())
    resolve_event(
        session,
        _zero_effect_event(),
        [Answer(question_id="q1", option_id="ok")],
    )
    assert session.state.finances == 52


def test_resolve_applies_high_band_income_net_of_upkeep() -> None:
    session = _session(config=GameConfig())
    session.state.tags["income_band"] = "high"
    resolve_event(
        session,
        _zero_effect_event(),
        [Answer(question_id="q1", option_id="ok")],
    )
    assert session.state.finances == 58


def test_resolve_emits_post_event_economy_action() -> None:
    session = _session(config=GameConfig())
    resolution = resolve_event(
        session,
        _zero_effect_event(),
        [Answer(question_id="q1", option_id="ok")],
    )
    economy = [
        action
        for action in resolution.client_actions
        if action.type == "post_event_economy"
    ]
    assert len(economy) == 1
    assert economy[0].args["income"] == 2
    assert economy[0].args["upkeep_children"] == 0
    assert economy[0].args["upkeep_housing"] == 0
    assert economy[0].args["net"] == 2
    assert economy[0].args["income_band"] is None
