"""AnswerBank exact-match coverage for V0 events (no decision_key)."""

from couple_simulator_engine.content.answers import AnswerBank
from couple_simulator_engine.content.definitions import (
    EventDefinition,
    OptionDefinition,
    OutcomeDefinition,
    QuestionDefinition,
)
from couple_simulator_engine.session import RecordedAnswer


def _event_two_questions() -> EventDefinition:
    return EventDefinition(
        id="weekend_trip",
        title="Weekend trip",
        description=None,
        tags=(),
        life_stage=None,
        eligibility=None,
        questions=(
            QuestionDefinition(
                id="go",
                text="Go?",
                options=(
                    OptionDefinition(id="yes", text="Yes"),
                    OptionDefinition(id="no", text="No"),
                ),
            ),
            QuestionDefinition(
                id="where",
                text="Where?",
                options=(
                    OptionDefinition(id="beach", text="Beach"),
                    OptionDefinition(id="city", text="City"),
                ),
            ),
        ),
        outcomes=(OutcomeDefinition(id="ok", when=None, actions=()),),
        default_actions=(),
        mismatch_actions=(),
    )


def test_resolve_for_event_returns_answers_when_fully_covered() -> None:
    event = _event_two_questions()
    bank = AnswerBank.from_recorded_answers(
        [
            RecordedAnswer(event_id="weekend_trip", question_id="go", option_id="yes"),
            RecordedAnswer(
                event_id="weekend_trip", question_id="where", option_id="beach"
            ),
        ]
    )
    resolved = bank.resolve_for_event(event)
    assert resolved is not None
    assert [(item.question_id, item.option_id) for item in resolved] == [
        ("go", "yes"),
        ("where", "beach"),
    ]


def test_resolve_for_event_returns_none_when_a_question_is_missing() -> None:
    event = _event_two_questions()
    bank = AnswerBank.from_recorded_answers(
        [RecordedAnswer(event_id="weekend_trip", question_id="go", option_id="yes")]
    )
    assert bank.resolve_for_event(event) is None


def test_resolve_for_event_last_entry_wins_for_same_question() -> None:
    event = _event_two_questions()
    bank = AnswerBank.from_recorded_answers(
        [
            RecordedAnswer(event_id="weekend_trip", question_id="go", option_id="no"),
            RecordedAnswer(
                event_id="weekend_trip", question_id="where", option_id="city"
            ),
            RecordedAnswer(event_id="weekend_trip", question_id="go", option_id="yes"),
        ]
    )
    resolved = bank.resolve_for_event(event)
    assert resolved is not None
    assert resolved[0].option_id == "yes"
    assert resolved[1].option_id == "city"


def test_has_coverage_for_is_true_iff_any_entry_has_event_id() -> None:
    bank = AnswerBank.from_recorded_answers(
        [RecordedAnswer(event_id="weekend_trip", question_id="go", option_id="yes")]
    )
    assert bank.has_coverage_for("weekend_trip") is True
    assert bank.has_coverage_for("burnout") is False
