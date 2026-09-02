"""Evaluation context for ``rules_evaluator`` (eligibility and ``when`` clauses)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from rules_evaluator import evaluate

from couple_simulator_engine.content.definitions import EventDefinition
from couple_simulator_engine.session import Answer, GameSession, RecordedAnswer


def evaluation_mode(session: GameSession) -> str:
    """``solo`` for Partner A runs, ``couple`` when the active player is Partner B."""
    if session.player is session.state.partner_b:
        return "couple"
    return "solo"


def build_evaluation_context(
    session: GameSession,
    event: EventDefinition,
    current_answers: Sequence[Answer | RecordedAnswer],
    *,
    flags: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the dict passed to ``rules_evaluator.evaluate`` (spec §11.2)."""
    if flags is None:
        flags_dict: dict[str, Any] = {}
    else:
        flags_dict = dict(flags)
        flags_dict.setdefault("has_mismatch", False)
        flags_dict.setdefault("answers_match", False)
    return {
        "state": session.state.to_dict(),
        "event_variables": session.event_variables,
        "answers": {answer.question_id: answer.option_id for answer in current_answers},
        "player": {
            "id": session.player.id,
            "name": session.player.name,
            "sex": session.player.sex.value,
        },
        "tags": list(event.tags),
        "flags": flags_dict,
        "mode": evaluation_mode(session),
    }


def should_apply(when: dict[str, Any] | None, ctx: dict[str, Any]) -> bool:
    """Return True when ``when`` is absent; otherwise delegate to ``evaluate``."""
    return evaluate(when, ctx)
