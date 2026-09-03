"""Resolve an event from submitted answers (spec §6.4)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from couple_simulator_engine.actions.registry import apply_action
from couple_simulator_engine.conditions import (
    build_evaluation_context,
    evaluation_mode,
    should_apply,
)
from couple_simulator_engine.content.definitions import (
    ActionDefinition,
    EventDefinition,
    OptionDefinition,
    QuestionDefinition,
)
from couple_simulator_engine.enums import SessionStatus
from couple_simulator_engine.resolution.conflict import ConflictResolver
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


def _complete_partner_a_answers(
    event: EventDefinition, partner_a_answers: Sequence[Answer] | None
) -> dict[str, Answer] | None:
    if partner_a_answers is None:
        return None
    by_question = _answers_by_question_id(partner_a_answers)
    for question in event.questions:
        answer = by_question.get(question.id)
        if answer is None:
            return None
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
    *,
    flags: Mapping[str, Any] | None = None,
) -> None:
    for action in actions:
        ctx = build_evaluation_context(session, event, current_answers, flags=flags)
        if should_apply(action.when, ctx):
            client_actions.extend(apply_action(action, ctx, session, session.rng))


def _game_finished(
    session: GameSession, client_actions: Sequence[ClientAction]
) -> bool:
    """Partial end check: reflect ``end_game`` (full checks are Epic 6)."""
    if session.status == SessionStatus.FINISHED:
        return True
    return any(action.type == "end_game" for action in client_actions)


def _effective_duo_answers(
    event: EventDefinition,
    live_by_question: dict[str, Answer],
    partner_a_by_question: dict[str, Answer],
    session: GameSession,
) -> tuple[list[Answer], dict[str, bool], list[tuple[str, str]]]:
    conflict = ConflictResolver()
    effective: list[Answer] = []
    disagreements: list[tuple[str, str]] = []
    has_mismatch = False
    for question in event.questions:
        live = live_by_question[question.id]
        partner_a = partner_a_by_question[question.id]
        if live.option_id == partner_a.option_id:
            effective.append(live)
            continue
        has_mismatch = True
        winner_id = conflict.resolve(
            partner_a.option_id,
            live.option_id,
            session.rng,
            session.config,
        )
        effective.append(Answer(question_id=question.id, option_id=winner_id))
        disagreements.append((winner_id, live.option_id))
    return (
        effective,
        {"has_mismatch": has_mismatch, "answers_match": not has_mismatch},
        disagreements,
    )


def _apply_couple_compatibility_delta(
    session: GameSession,
    event: EventDefinition,
    effective_answers: Sequence[Answer],
    client_actions: list[ClientAction],
    *,
    flags: Mapping[str, Any],
) -> None:
    if flags["has_mismatch"]:
        delta = -session.config.compatibility_mismatch_penalty
    else:
        delta = session.config.compatibility_match_bonus
    ctx = build_evaluation_context(session, event, effective_answers, flags=flags)
    client_actions.extend(
        apply_action(
            ActionDefinition(
                type="modify_stat",
                args={"variable": "compatibility", "delta": delta},
            ),
            ctx,
            session,
            session.rng,
        )
    )


def _apply_conflict_personal_deltas(
    session: GameSession, disagreements: Sequence[tuple[str, str]]
) -> None:
    bonus = session.config.conflict_winner_bonus
    penalty = session.config.conflict_loser_penalty
    for winner_option_id, partner_b_option_id in disagreements:
        if winner_option_id == partner_b_option_id:
            winner = session.state.partner_b
            loser = session.state.partner_a
        else:
            winner = session.state.partner_a
            loser = session.state.partner_b
        winner.set_simulation_relation_happiness(
            winner.simulation_relation_happiness + bonus
        )
        loser.set_simulation_relation_happiness(
            loser.simulation_relation_happiness - penalty
        )


def resolve_event(
    session: GameSession,
    event: EventDefinition,
    answers: Sequence[Answer],
    partner_a_answers: Sequence[Answer] | None = None,
) -> EventResolution:
    """Run option actions, matching outcomes, then defaults; update session."""
    live_by_question = _validate_answers(event, answers)
    submitted_ordered = [live_by_question[question.id] for question in event.questions]
    _open_event_if_needed(session, event)

    bank_answers = partner_a_answers if event.use_answer_bank else None
    partner_a_by_question = (
        _complete_partner_a_answers(event, bank_answers)
        if evaluation_mode(session) == "couple"
        else None
    )

    flags: dict[str, bool] | None = None
    disagreements: list[tuple[str, str]] = []
    if partner_a_by_question is not None:
        effective_ordered, flags, disagreements = _effective_duo_answers(
            event, live_by_question, partner_a_by_question, session
        )
    else:
        effective_ordered = submitted_ordered

    client_actions: list[ClientAction] = []
    for question, answer in zip(event.questions, effective_ordered, strict=True):
        option = _option_for(question, answer.option_id)
        _apply_actions(
            option.actions,
            session,
            event,
            effective_ordered,
            client_actions,
            flags=flags,
        )

    if flags is not None:
        _apply_couple_compatibility_delta(
            session, event, effective_ordered, client_actions, flags=flags
        )
        _apply_conflict_personal_deltas(session, disagreements)
        if flags["has_mismatch"]:
            _apply_actions(
                event.mismatch_actions,
                session,
                event,
                effective_ordered,
                client_actions,
                flags=flags,
            )

    ctx = build_evaluation_context(session, event, effective_ordered, flags=flags)
    applied = matching_outcomes(event, ctx)
    if applied:
        for outcome in applied:
            _apply_actions(
                outcome.actions,
                session,
                event,
                effective_ordered,
                client_actions,
                flags=flags,
            )
    else:
        _apply_actions(
            event.default_actions,
            session,
            event,
            effective_ordered,
            client_actions,
            flags=flags,
        )

    snapshot = session.state.to_dict()
    for answer in submitted_ordered:
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
        answers_recorded=list(submitted_ordered),
        game_finished=_game_finished(session, client_actions),
    )
