"""Resolve an event from submitted answers (spec §6.4)."""

from __future__ import annotations

from collections.abc import Sequence

from couple_simulator_engine.actions.registry import apply_action
from couple_simulator_engine.conditions import build_evaluation_context, should_apply
from couple_simulator_engine.content.definitions import (
    ActionDefinition,
    EventDefinition,
    OptionDefinition,
    QuestionDefinition,
)
from couple_simulator_engine.enums import SessionStatus
from couple_simulator_engine.resolution.outcomes import matching_outcomes
from couple_simulator_engine.session import (
    Answer,
    ClientAction,
    EventResolution,
    GameSession,
    RecordedAnswer,
)


class AnswerValidationError(ValueError):
    """Raised when submitted answers do not cover required questions."""


def _answers_by_question_id(answers: Sequence[Answer]) -> dict[str, Answer]:
    by_question: dict[str, Answer] = {}
    for answer in answers:
        if answer.question_id in by_question:
            raise AnswerValidationError(
                f"Duplicate answer for question '{answer.question_id}'"
            )
        by_question[answer.question_id] = answer
    return by_question


def _option_for(question: QuestionDefinition, option_id: str) -> OptionDefinition:
    for option in question.options:
        if option.id == option_id:
            return option
    raise AnswerValidationError(
        f"Unknown option '{option_id}' for question '{question.id}'"
    )


def _validate_answers(
    event: EventDefinition, answers: Sequence[Answer]
) -> dict[str, Answer]:
    by_question = _answers_by_question_id(answers)
    for question in event.questions:
        answer = by_question.get(question.id)
        if answer is None:
            raise AnswerValidationError(
                f"Missing required answer for question '{question.id}'"
            )
        _option_for(question, answer.option_id)
    return by_question


def _open_event_if_needed(session: GameSession, event: EventDefinition) -> None:
    if session.current_event_id != event.id:
        session.event_variables.clear()
        session.current_event_id = event.id


def _apply_actions(
    actions: Sequence[ActionDefinition],
    session: GameSession,
    event: EventDefinition,
    current_answers: Sequence[Answer],
    client_actions: list[ClientAction],
) -> None:
    for action in actions:
        ctx = build_evaluation_context(session, event, current_answers)
        if should_apply(action.when, ctx):
            client_actions.extend(
                apply_action(action, ctx, session, session.rng)
            )


def _game_finished(
    session: GameSession, client_actions: Sequence[ClientAction]
) -> bool:
    """Partial end check: reflect ``end_game`` (full checks are Epic 6)."""
    if session.status == SessionStatus.FINISHED:
        return True
    return any(action.type == "end_game" for action in client_actions)


def resolve_event(
    session: GameSession,
    event: EventDefinition,
    answers: Sequence[Answer],
) -> EventResolution:
    """Run option actions, matching outcomes, then defaults; update session."""
    by_question = _validate_answers(event, answers)
    ordered_answers = [by_question[question.id] for question in event.questions]
    _open_event_if_needed(session, event)

    client_actions: list[ClientAction] = []
    for question in event.questions:
        answer = by_question[question.id]
        option = _option_for(question, answer.option_id)
        _apply_actions(
            option.actions, session, event, ordered_answers, client_actions
        )

    ctx = build_evaluation_context(session, event, ordered_answers)
    applied = matching_outcomes(event, ctx)
    if applied:
        for outcome in applied:
            _apply_actions(
                outcome.actions, session, event, ordered_answers, client_actions
            )
    else:
        _apply_actions(
            event.default_actions, session, event, ordered_answers, client_actions
        )
    # mismatch_actions are not executed in V0 solo.

    snapshot = session.state.to_dict()
    for answer in ordered_answers:
        session.answers.append(
            RecordedAnswer(
                event_id=event.id,
                question_id=answer.question_id,
                option_id=answer.option_id,
                state_snapshot=snapshot,
            )
        )
    session.events_played += 1
    session.events_played_ids.append(event.id)
    session.event_variables.clear()
    session.current_event_id = None

    return EventResolution(
        event_id=event.id,
        applied_outcome_ids=[outcome.id for outcome in applied],
        client_actions=client_actions,
        state=session.state,
        answers_recorded=list(ordered_answers),
        game_finished=_game_finished(session, client_actions),
    )
