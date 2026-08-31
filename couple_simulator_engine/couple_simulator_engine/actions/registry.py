"""Register and dispatch ``ActionDefinition`` handlers (spec §8.7)."""

from __future__ import annotations

from couple_simulator_engine.actions.types import (
    ActionHandler,
    EvaluationContext,
    UnknownActionTypeError,
)
from couple_simulator_engine.content.definitions import ActionDefinition
from couple_simulator_engine.rng import SeededRNG
from couple_simulator_engine.session import ClientAction, GameSession

_ACTION_HANDLERS: dict[str, ActionHandler] = {}


def register_action_handler(action_type: str, handler: ActionHandler) -> None:
    _ACTION_HANDLERS[action_type] = handler


def apply_action(
    action: ActionDefinition,
    ctx: EvaluationContext,
    session: GameSession,
    rng: SeededRNG,
) -> list[ClientAction]:
    if not _ACTION_HANDLERS:
        from couple_simulator_engine.actions import handlers as _handlers

        _ = _handlers
    if action.type not in _ACTION_HANDLERS:
        raise UnknownActionTypeError(action.type)
    return _ACTION_HANDLERS[action.type](action.args, ctx, session, rng)
