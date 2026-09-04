"""Unified action pipeline (spec §8)."""

from couple_simulator_engine.actions.distributions import resolve_value
from couple_simulator_engine.actions.handlers import (
    handle_add_conversation,
    handle_add_timeline_entry,
    handle_advance_life_stage,
    handle_end_game,
    handle_modify_stat,
    handle_set_event_var,
    handle_set_housing,
    handle_set_mascot,
    handle_set_stat,
    handle_set_tag,
    handle_update_avatar,
)
from couple_simulator_engine.actions.registry import (
    apply_action,
    register_action_handler,
)
from couple_simulator_engine.actions.types import ActionHandler, UnknownActionTypeError

__all__ = [
    "ActionHandler",
    "UnknownActionTypeError",
    "apply_action",
    "handle_add_conversation",
    "handle_add_timeline_entry",
    "handle_advance_life_stage",
    "handle_end_game",
    "handle_modify_stat",
    "handle_set_event_var",
    "handle_set_housing",
    "handle_set_mascot",
    "handle_set_stat",
    "handle_set_tag",
    "handle_update_avatar",
    "register_action_handler",
    "resolve_value",
]
