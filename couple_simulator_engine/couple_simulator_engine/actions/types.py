"""Action handler protocol and errors."""

from __future__ import annotations

from typing import Any, Protocol

from couple_simulator_engine.rng import SeededRNG
from couple_simulator_engine.session import ClientAction, GameSession

EvaluationContext = dict[str, Any]


class UnknownActionTypeError(Exception):
    """Raised when ``apply_action`` is called with an unregistered type."""

    def __init__(self, action_type: str) -> None:
        self.action_type = action_type
        super().__init__(f"Unknown action type '{action_type}'")


class ActionHandler(Protocol):
    def __call__(
        self,
        args: dict[str, Any],
        ctx: EvaluationContext,
        session: GameSession,
        rng: SeededRNG,
    ) -> list[ClientAction]: ...


__all__ = [
    "ActionHandler",
    "EvaluationContext",
    "UnknownActionTypeError",
]
