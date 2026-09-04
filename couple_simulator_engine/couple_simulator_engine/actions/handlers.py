"""V0 action handlers. Importing this module registers them."""

from __future__ import annotations

from typing import Any

from couple_simulator_engine.actions.distributions import resolve_value
from couple_simulator_engine.actions.registry import register_action_handler
from couple_simulator_engine.actions.types import EvaluationContext
from couple_simulator_engine.clamp import clamp_stat
from couple_simulator_engine.enums import (
    HousingQuality,
    HousingType,
    LifeStage,
    RelationshipStatus,
    SessionStatus,
)
from couple_simulator_engine.rng import SeededRNG
from couple_simulator_engine.session import ClientAction, GameSession, TimelineEntry
from couple_simulator_engine.state import Housing, Mascot

_PLAYER_NAME_PLACEHOLDER = "{{player.name}}"
_PARTNER_A_NAME_PLACEHOLDER = "{{partner_a.name}}"
_PARTNER_B_NAME_PLACEHOLDER = "{{partner_b.name}}"


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


def _interpolate_templates(
    template: str,
    ctx: EvaluationContext,
    session: GameSession,
) -> str:
    result = template.replace(_PLAYER_NAME_PLACEHOLDER, _player_name(ctx, session))
    result = result.replace(
        _PARTNER_A_NAME_PLACEHOLDER,
        session.state.partner_a.name,
    )
    return result.replace(
        _PARTNER_B_NAME_PLACEHOLDER,
        session.state.partner_b.name,
    )


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


def handle_set_stat(
    args: dict[str, Any],
    ctx: EvaluationContext,
    session: GameSession,
    rng: SeededRNG,
) -> list[ClientAction]:
    variable = args["variable"]
    requested = _as_int_delta(resolve_value(args["value"], rng))
    if variable == "age":
        assigned = clamp_stat("age", requested)
        for partner in session.state.partners():
            partner.set_simulation_age(assigned)
        new = session.state.age
    elif variable == "compatibility":
        assigned = clamp_stat("compatibility", requested)
        for partner in session.state.partners():
            partner.set_simulation_relation_happiness(assigned)
        new = session.state.compatibility
    else:
        new = session.state.set_stat(variable, requested)
    return [
        ClientAction(
            type="set_stat",
            args={
                "variable": variable,
                "value": new,
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
    payload: dict[str, Any] = {"speaker": args["speaker"]}
    raw_params = args.get("params")
    if isinstance(raw_params, dict):
        resolved_params: dict[str, Any] = {}
        for key, value in raw_params.items():
            if isinstance(value, str):
                resolved_params[key] = _interpolate_templates(value, ctx, session)
            else:
                resolved_params[key] = value
        payload["params"] = resolved_params
    if "text" in args:
        payload["text"] = _interpolate_templates(str(args["text"]), ctx, session)
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


def _require_non_empty_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid {field_name}: {value!r}")
    return value


def _housing_payload(housing: Housing) -> dict[str, str]:
    return {
        "place": housing.place,
        "type": housing.type.value,
        "quality": housing.quality.value,
    }


def _mascot_payload(mascot: Mascot | None) -> dict[str, str] | None:
    if mascot is None:
        return None
    return {"species": mascot.species, "name": mascot.name}


def handle_set_housing(
    args: dict[str, Any],
    ctx: EvaluationContext,
    session: GameSession,
    rng: SeededRNG,
) -> list[ClientAction]:
    place = _require_non_empty_str(args["place"], "place")
    housing_type = HousingType(args["type"])
    quality = HousingQuality(args["quality"])
    session.state.housing = Housing(place=place, type=housing_type, quality=quality)
    return [
        ClientAction(type="set_housing", args=_housing_payload(session.state.housing)),
    ]


def handle_set_mascot(
    args: dict[str, Any],
    ctx: EvaluationContext,
    session: GameSession,
    rng: SeededRNG,
) -> list[ClientAction]:
    clearing = "mascot" in args and args["mascot"] is None
    species = args.get("species")
    name = args.get("name")
    if clearing:
        if species is not None or name is not None:
            raise ValueError("Cannot mix mascot clear with species or name")
        session.state.mascot = None
    else:
        if species is None or name is None:
            raise ValueError("set_mascot requires species and name, or mascot null")
        session.state.mascot = Mascot(
            species=_require_non_empty_str(species, "species"),
            name=_require_non_empty_str(name, "name"),
        )
    return [
        ClientAction(
            type="set_mascot",
            args={"mascot": _mascot_payload(session.state.mascot)},
        )
    ]


def _tag_key(value: Any) -> str:
    key = _require_non_empty_str(value, "key")
    if "/" in key:
        raise ValueError(f"Invalid key: {value!r}")
    return key


def handle_set_relationship_status(
    args: dict[str, Any],
    ctx: EvaluationContext,
    session: GameSession,
    rng: SeededRNG,
) -> list[ClientAction]:
    status_raw = args["status"]
    status = (
        status_raw
        if isinstance(status_raw, RelationshipStatus)
        else RelationshipStatus(status_raw)
    )
    session.state.relationship_status = status
    return [
        ClientAction(
            type="set_relationship_status",
            args={"status": status.value},
        )
    ]


def handle_set_tag(
    args: dict[str, Any],
    ctx: EvaluationContext,
    session: GameSession,
    rng: SeededRNG,
) -> list[ClientAction]:
    key = _tag_key(args["key"])
    raw_value = args["value"]
    if raw_value is None:
        session.state.tags.pop(key, None)
        stored: Any = None
    else:
        stored = resolve_value(raw_value, rng)
        session.state.tags[key] = stored
    return [ClientAction(type="set_tag", args={"key": key, "value": stored})]


_AVATAR_PLAYERS = frozenset({"partner_a", "partner_b"})
_AVATAR_PROBABILITY_KEYS = frozenset(
    {"accessoriesProbability", "facialHairProbability"}
)
_AVATAR_VARIANT_KEYS = frozenset(
    {
        "topVariant",
        "eyesVariant",
        "eyebrowsVariant",
        "mouthVariant",
        "facialHairVariant",
        "clothesVariant",
        "accessoriesVariant",
        "skinColor",
        "hairColor",
        "facialHairColor",
        "clothesColor",
    }
)
_AVATAR_ATTRIBUTE_KEYS = _AVATAR_VARIANT_KEYS | _AVATAR_PROBABILITY_KEYS


def _avatar_player_role(value: Any) -> str:
    role = _require_non_empty_str(value, "player")
    if role not in _AVATAR_PLAYERS:
        raise ValueError(f"Invalid player: {value!r}")
    return role


def _avatar_attribute(value: Any) -> str:
    attribute = _require_non_empty_str(value, "attribute")
    if attribute not in _AVATAR_ATTRIBUTE_KEYS:
        raise ValueError(f"Invalid attribute: {value!r}")
    return attribute


def _avatar_attribute_value(attribute: str, value: Any) -> str | int:
    if attribute in _AVATAR_PROBABILITY_KEYS:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"Invalid value: {value!r}")
        if value < 0 or value > 100:
            raise ValueError(f"Invalid value: {value!r}")
        return value
    return _require_non_empty_str(value, "value")


def handle_update_avatar(
    args: dict[str, Any],
    ctx: EvaluationContext,
    session: GameSession,
    rng: SeededRNG,
) -> list[ClientAction]:
    player_role = _avatar_player_role(args["player"])
    attribute = _avatar_attribute(args["attribute"])
    stored = _avatar_attribute_value(attribute, args["value"])
    partner = (
        session.state.partner_b
        if player_role == "partner_b"
        else session.state.partner_a
    )
    existing = partner.avatar_config
    current = dict(existing) if existing is not None else {}
    current[attribute] = stored
    partner.avatar_config = current
    return [
        ClientAction(
            type="update_avatar",
            args={
                "player": player_role,
                "attribute": attribute,
                "value": stored,
                "avatar_config": dict(current),
            },
        )
    ]


register_action_handler("modify_stat", handle_modify_stat)
register_action_handler("set_stat", handle_set_stat)
register_action_handler("set_event_var", handle_set_event_var)
register_action_handler("add_conversation", handle_add_conversation)
register_action_handler("add_timeline_entry", handle_add_timeline_entry)
register_action_handler("advance_life_stage", handle_advance_life_stage)
register_action_handler("end_game", handle_end_game)
register_action_handler("set_housing", handle_set_housing)
register_action_handler("set_mascot", handle_set_mascot)
register_action_handler("set_relationship_status", handle_set_relationship_status)
register_action_handler("set_tag", handle_set_tag)
register_action_handler("update_avatar", handle_update_avatar)
