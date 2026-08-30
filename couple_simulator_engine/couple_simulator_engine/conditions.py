"""Evaluation context for ``rules_evaluator`` (eligibility and ``when`` clauses)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from rules_evaluator import evaluate

from couple_simulator_engine.content.definitions import EventDefinition
from couple_simulator_engine.session import Answer, GameSession, RecordedAnswer


def build_evaluation_context(
    session: GameSession,
    event: EventDefinition,
    current_answers: Sequence[Answer | RecordedAnswer],
) -> dict[str, Any]:
    """Build the dict passed to ``rules_evaluator.evaluate`` (spec §11.2)."""
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
        "flags": {},
        "mode": "solo",
    }


def should_apply(when: dict[str, Any] | None, ctx: dict[str, Any]) -> bool:
    """Return True when ``when`` is absent; otherwise delegate to ``evaluate``."""
    return evaluate(when, ctx)
