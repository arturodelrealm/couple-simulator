"""Event resolution pipeline (spec §6.4, P2)."""

import pytest

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.content.catalog import (
    load_catalog,
    package_events_directory,
)
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
        current_event_id=current_event_id,
    )


def _catalog_event(event_id: str) -> EventDefinition:
    catalog = load_catalog(package_events_directory())
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
    assert session.state.quality_of_life == 60
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
    assert session.state.career == 70
    assert session.state.quality_of_life == 45


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
                        args={"variable": "career", "delta": 2},
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
    assert session.state.career == 52


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
        and action.args.get("text")
        == "We leave the housing question open for now."
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
