"""Construct content definition dataclasses without JSON."""

from dataclasses import FrozenInstanceError

import pytest

from couple_simulator_engine.content.definitions import (
    ActionDefinition,
    EventDefinition,
    OptionDefinition,
    OutcomeDefinition,
    QuestionDefinition,
)
from couple_simulator_engine.enums import LifeStage


def test_definition_dataclasses_are_frozen() -> None:
    action = ActionDefinition(
        type="modify_stat",
        args={"variable": "finances", "delta": 1},
    )
    option = OptionDefinition(id="yes", text="Yes", actions=(action,))
    question = QuestionDefinition(id="q1", text="Question?", options=(option,))
    outcome = OutcomeDefinition(id="ok", when=None, actions=(action,))
    event = EventDefinition(
        id="sample",
        title="Sample",
        description=None,
        tags=("tag",),
        life_stage=LifeStage.YOUTH,
        eligibility={
            "type": "compare",
            "path": "state/finances",
            "op": "gte",
            "value": 40,
        },
        questions=(question,),
        outcomes=(outcome,),
        default_actions=(),
        mismatch_actions=(),
    )

    with pytest.raises(FrozenInstanceError):
        action.type = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        option.text = "No"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        question.id = "q2"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        outcome.id = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        event.title = "Changed"  # type: ignore[misc]


def test_event_definition_fields_match_schema() -> None:
    action = ActionDefinition(
        type="set_event_var",
        args={"variable": "home_desire", "value": 3},
        when={"type": "compare", "path": "answers/q1", "op": "eq", "value": "yes"},
    )
    event = EventDefinition(
        id="buy_house_light",
        title="Buy a house?",
        description="Housing choice",
        tags=("financial", "housing"),
        life_stage=None,
        eligibility=None,
        questions=(
            QuestionDefinition(
                id="want_to_buy",
                text="Would you like to buy a house?",
                options=(
                    OptionDefinition(id="yes", text="Yes", actions=(action,)),
                    OptionDefinition(id="no", text="No"),
                ),
            ),
        ),
        outcomes=(OutcomeDefinition(id="purchase", when=None, actions=()),),
        default_actions=(),
        mismatch_actions=(),
        weight=1.0,
        max_occurrences=1,
    )

    assert event.id == "buy_house_light"
    assert event.mismatch_actions == ()
    assert event.life_stage is None
    assert event.questions[0].options[0].actions[0].when is not None
    assert event.questions[0].options[1].actions == ()
