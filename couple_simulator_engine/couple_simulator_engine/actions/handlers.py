"""V0 action handlers. Importing this module registers them."""

from __future__ import annotations

from typing import Any

from couple_simulator_engine.actions.distributions import resolve_value
from couple_simulator_engine.actions.registry import register_action_handler
from couple_simulator_engine.actions.types import EvaluationContext
from couple_simulator_engine.enums import LifeStage, SessionStatus
from couple_simulator_engine.rng import SeededRNG
from couple_simulator_engine.session import ClientAction, GameSession, TimelineEntry

_PLAYER_NAME_PLACEHOLDER = "{{player.name}}"


def _as_int_delta(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError(f"Invalid numeric delta: {value!r}")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))
    raise ValueError(f"Invalid numeric delta: {value!r}")


def _player_name(ctx: EvaluationContext, session: GameSession) -> str:
    player = ctx.get("player")
    if isinstance(player, dict) and "name" in player:
        return str(player["name"])
    return session.player.name


def _interpolate_player_name(template: str, name: str) -> str:
    return template.replace(_PLAYER_NAME_PLACEHOLDER, name)


def handle_modify_stat(
    args: dict[str, Any],
    ctx: EvaluationContext,
    session: GameSession,
    rng: SeededRNG,
) -> list[ClientAction]:
    variable = args["variable"]
    delta = _as_int_delta(resolve_value(args["delta"], rng))
    old = getattr(session.state, variable)
    if variable == "age":
        for partner in session.state.partners():
            partner.set_simulation_age(partner.simulation_age + delta)
        new = session.state.age
    elif variable == "compatibility":
        for partner in session.state.partners():
            partner.set_simulation_relation_happiness(
                partner.simulation_relation_happiness + delta
            )
        new = session.state.compatibility
    else:
        new = session.state.set_stat(variable, old + delta)
    return [
        ClientAction(
            type="modify_stat",
            args={
                "variable": variable,
                "delta": new - old,
                "new_value": new,
            },
        )
    ]


def handle_set_event_var(
    args: dict[str, Any],
    ctx: EvaluationContext,
    session: GameSession,
    rng: SeededRNG,
) -> list[ClientAction]:
    session.event_variables[args["variable"]] = resolve_value(args["value"], rng)
    return []


def handle_add_conversation(
    args: dict[str, Any],
    ctx: EvaluationContext,
    session: GameSession,
    rng: SeededRNG,
) -> list[ClientAction]:
    name = _player_name(ctx, session)
    payload: dict[str, Any] = {"speaker": args["speaker"]}
    raw_params = args.get("params")
    if isinstance(raw_params, dict):
        resolved_params: dict[str, Any] = {}
        for key, value in raw_params.items():
            if isinstance(value, str):
                resolved_params[key] = _interpolate_player_name(value, name)
            else:
                resolved_params[key] = value
        payload["params"] = resolved_params
    if "text" in args:
        payload["text"] = _interpolate_player_name(str(args["text"]), name)
    if "text_key" in args:
        payload["text_key"] = args["text_key"]
    return [ClientAction(type="add_conversation", args=payload)]


def handle_add_timeline_entry(
    args: dict[str, Any],
    ctx: EvaluationContext,
    session: GameSession,
    rng: SeededRNG,
) -> list[ClientAction]:
    title_key = args.get("title_key")
    description_key = args.get("description_key")
    title = str(title_key) if title_key is not None else args["title"]
    if description_key is not None:
        description = str(description_key)
    else:
        description = args.get("description")
    entry = TimelineEntry(
        title=title,
        category=args["category"],
        age=session.state.age,
        description=description,
    )
    session.timeline.append(entry)
    client_args: dict[str, Any] = {
        "title": entry.title,
        "category": entry.category,
        "age": entry.age,
    }
    if entry.description is not None:
        client_args["description"] = entry.description
    if title_key is not None:
        client_args["title_key"] = title_key
    if description_key is not None:
        client_args["description_key"] = description_key
    return [ClientAction(type="add_timeline_entry", args=client_args)]


def handle_advance_life_stage(
    args: dict[str, Any],
    ctx: EvaluationContext,
    session: GameSession,
    rng: SeededRNG,
) -> list[ClientAction]:
    from_stage = session.state.life_stage
    to_raw = args["to"]
    to_stage = to_raw if isinstance(to_raw, LifeStage) else LifeStage(to_raw)
    session.state.life_stage = to_stage
    return [
        ClientAction(
            type="advance_life_stage",
            args={"from": from_stage.value, "to": to_stage.value},
        )
    ]


def handle_end_game(
    args: dict[str, Any],
    ctx: EvaluationContext,
    session: GameSession,
    rng: SeededRNG,
) -> list[ClientAction]:
    reason = args.get("reason")
    session.status = SessionStatus.FINISHED
    session.end_reason = reason
    return [ClientAction(type="end_game", args={"reason": reason})]


register_action_handler("modify_stat", handle_modify_stat)
register_action_handler("set_event_var", handle_set_event_var)
register_action_handler("add_conversation", handle_add_conversation)
register_action_handler("add_timeline_entry", handle_add_timeline_entry)
register_action_handler("advance_life_stage", handle_advance_life_stage)
register_action_handler("end_game", handle_end_game)
