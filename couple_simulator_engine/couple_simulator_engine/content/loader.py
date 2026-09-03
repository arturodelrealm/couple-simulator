"""Parse event JSON files into `EventDefinition` instances."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from couple_simulator_engine.content.definitions import (
    ActionDefinition,
    EventDefinition,
    OptionDefinition,
    OutcomeDefinition,
    QuestionDefinition,
    TextField,
    TextPresentation,
)
from couple_simulator_engine.enums import LifeStage

DEFAULT_WEIGHT = 1.0
DEFAULT_MAX_OCCURRENCES = 1


class ContentParseError(ValueError):
    """Raised when an event JSON file cannot be parsed into definitions."""


class DuplicateEventIdError(ValueError):
    """Raised when two event files declare the same `id`."""


def load_event_file(path: str | Path) -> EventDefinition:
    """Parse a single JSON file into an `EventDefinition`."""
    file_path = Path(path)
    source = str(file_path)
    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContentParseError(f"Cannot read event file: {source}") from exc
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ContentParseError(
            f"Invalid JSON in {source}: {exc.msg} (line {exc.lineno})"
        ) from exc
    if not isinstance(data, dict):
        raise ContentParseError(f"Event JSON root must be an object in {source}")
    return _parse_event(data, source=source)


def load_event_directory(path: str | Path) -> list[EventDefinition]:
    """Parse every `*.json` file in a directory (non-recursive)."""
    directory = Path(path)
    if not directory.is_dir():
        raise ContentParseError(f"Events path is not a directory: {directory}")

    events: list[EventDefinition] = []
    seen_ids: dict[str, Path] = {}
    for file_path in sorted(directory.glob("*.json")):
        event = load_event_file(file_path)
        previous = seen_ids.get(event.id)
        if previous is not None:
            raise DuplicateEventIdError(
                f"Duplicate event id {event.id!r}: "
                f"{file_path} conflicts with {previous}"
            )
        seen_ids[event.id] = file_path
        events.append(event)
    return events


def _parse_event(data: dict[str, Any], *, source: str) -> EventDefinition:
    event_id = _require_str(data, "id", source=source, event_id=None)
    ctx = {"source": source, "event_id": event_id}
    title = _require_str(data, "title", **ctx)
    if "questions" not in data:
        raise ContentParseError(
            _format_error("Missing required field 'questions'", **ctx)
        )
    questions_raw = data["questions"]
    if not isinstance(questions_raw, list):
        raise ContentParseError(
            _format_error("Field 'questions' must be a list", **ctx)
        )

    questions = tuple(
        _parse_question(item, index=index, **ctx)
        for index, item in enumerate(questions_raw)
    )
    outcomes_raw = data.get("outcomes", [])
    if not isinstance(outcomes_raw, list):
        raise ContentParseError(_format_error("Field 'outcomes' must be a list", **ctx))
    outcomes = tuple(
        _parse_outcome(item, index=index, **ctx)
        for index, item in enumerate(outcomes_raw)
    )

    return EventDefinition(
        id=event_id,
        title=title,
        description=_optional_str(data.get("description"), field="description", **ctx),
        tags=_parse_str_tuple(data.get("tags", []), field="tags", **ctx),
        life_stage=_parse_life_stage(data.get("life_stage"), **ctx),
        eligibility=_optional_condition(
            data.get("eligibility"), field="eligibility", **ctx
        ),
        questions=questions,
        outcomes=outcomes,
        default_actions=_parse_actions(
            data.get("default_actions", []),
            field="default_actions",
            **ctx,
        ),
        mismatch_actions=_parse_actions(
            data.get("mismatch_actions", []),
            field="mismatch_actions",
            **ctx,
        ),
        weight=_parse_float(data.get("weight", DEFAULT_WEIGHT), field="weight", **ctx),
        max_occurrences=_parse_int(
            data.get("max_occurrences", DEFAULT_MAX_OCCURRENCES),
            field="max_occurrences",
            **ctx,
        ),
    )


def _parse_text_field(
    value: Any,
    *,
    field: str,
    source: str,
    event_id: str,
) -> TextField:
    """Parse a plain i18n key string or a ``TextPresentation`` object."""
    if isinstance(value, str):
        if not value:
            raise ContentParseError(
                _format_error(
                    f"Field '{field}' must be a non-empty string",
                    source=source,
                    event_id=event_id,
                )
            )
        return value
    if isinstance(value, dict):
        if "default_key" not in value or not isinstance(value["default_key"], str):
            raise ContentParseError(
                _format_error(
                    f"Field '{field}' object requires a non-empty string 'default_key'",
                    source=source,
                    event_id=event_id,
                )
            )
        if not value["default_key"]:
            raise ContentParseError(
                _format_error(
                    f"Field '{field}' object requires a non-empty string 'default_key'",
                    source=source,
                    event_id=event_id,
                )
            )
        by_role = _parse_text_variant_dict(
            value.get("by_role"), variant="by_role", field=field,
            source=source, event_id=event_id,
        )
        by_sex = _parse_text_variant_dict(
            value.get("by_sex"), variant="by_sex", field=field,
            source=source, event_id=event_id,
        )
        return TextPresentation(
            default_key=value["default_key"],
            by_role=by_role,
            by_sex=by_sex,
        )
    raise ContentParseError(
        _format_error(
            f"Field '{field}' must be a string or TextPresentation object",
            source=source,
            event_id=event_id,
        )
    )


def _parse_text_variant_dict(
    value: Any,
    *,
    variant: str,
    field: str,
    source: str,
    event_id: str,
) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ContentParseError(
            _format_error(
                f"Field '{field}.{variant}' must be an object",
                source=source,
                event_id=event_id,
            )
        )
    for k, v in value.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ContentParseError(
                _format_error(
                    f"Field '{field}.{variant}' must have string keys and values",
                    source=source,
                    event_id=event_id,
                )
            )
    return dict(value)


def _parse_question(
    data: Any,
    *,
    index: int,
    source: str,
    event_id: str,
) -> QuestionDefinition:
    ctx = {"source": source, "event_id": event_id}
    if not isinstance(data, dict):
        raise ContentParseError(
            _format_error(f"Question at index {index} must be an object", **ctx)
        )
    question_id = _require_str(data, "id", **ctx)
    if "text" not in data:
        raise ContentParseError(
            _format_error("Missing required field 'text'", **ctx)
        )
    text = _parse_text_field(data["text"], field="text", **ctx)
    if "options" not in data or not isinstance(data["options"], list):
        raise ContentParseError(
            _format_error(
                f"Question {question_id!r} requires a list field 'options'",
                **ctx,
            )
        )
    if len(data["options"]) < 1:
        raise ContentParseError(
            _format_error(
                f"Question {question_id!r} requires at least one option",
                **ctx,
            )
        )
    options = tuple(
        _parse_option(item, question_id=question_id, index=opt_index, **ctx)
        for opt_index, item in enumerate(data["options"])
    )
    return QuestionDefinition(id=question_id, text=text, options=options)


def _parse_option(
    data: Any,
    *,
    question_id: str,
    index: int,
    source: str,
    event_id: str,
) -> OptionDefinition:
    ctx = {"source": source, "event_id": event_id}
    if not isinstance(data, dict):
        raise ContentParseError(
            _format_error(
                f"Option at index {index} of question {question_id!r} "
                "must be an object",
                **ctx,
            )
        )
    option_id = _require_str(data, "id", **ctx)
    if "text" not in data:
        raise ContentParseError(
            _format_error("Missing required field 'text'", **ctx)
        )
    text = _parse_text_field(data["text"], field="text", **ctx)
    actions = _parse_actions(
        data.get("actions", []),
        field=f"option {option_id!r} actions",
        **ctx,
    )
    return OptionDefinition(id=option_id, text=text, actions=actions)


def _parse_outcome(
    data: Any,
    *,
    index: int,
    source: str,
    event_id: str,
) -> OutcomeDefinition:
    ctx = {"source": source, "event_id": event_id}
    if not isinstance(data, dict):
        raise ContentParseError(
            _format_error(f"Outcome at index {index} must be an object", **ctx)
        )
    outcome_id = _require_str(data, "id", **ctx)
    return OutcomeDefinition(
        id=outcome_id,
        when=_optional_condition(
            data.get("when"), field=f"outcome {outcome_id!r} when", **ctx
        ),
        actions=_parse_actions(
            data.get("actions", []),
            field=f"outcome {outcome_id!r} actions",
            **ctx,
        ),
    )


def _parse_actions(
    data: Any,
    *,
    field: str,
    source: str,
    event_id: str,
) -> tuple[ActionDefinition, ...]:
    ctx = {"source": source, "event_id": event_id}
    if not isinstance(data, list):
        raise ContentParseError(_format_error(f"Field '{field}' must be a list", **ctx))
    return tuple(
        _parse_action(item, field=field, index=index, **ctx)
        for index, item in enumerate(data)
    )


def _parse_action(
    data: Any,
    *,
    field: str,
    index: int,
    source: str,
    event_id: str,
) -> ActionDefinition:
    ctx = {"source": source, "event_id": event_id}
    if not isinstance(data, dict):
        raise ContentParseError(
            _format_error(
                f"Action at index {index} in '{field}' must be an object", **ctx
            )
        )
    action_type = _require_str(data, "type", **ctx)
    args = data.get("args", {})
    if not isinstance(args, dict):
        raise ContentParseError(
            _format_error(
                f"Action '{action_type}' field 'args' must be an object", **ctx
            )
        )
    return ActionDefinition(
        type=action_type,
        args=dict(args),
        when=_optional_condition(
            data.get("when"), field=f"action '{action_type}' when", **ctx
        ),
    )


def _require_str(
    data: dict[str, Any],
    field: str,
    *,
    source: str,
    event_id: str | None,
) -> str:
    if field not in data:
        raise ContentParseError(
            _format_error(
                f"Missing required field '{field}'", source=source, event_id=event_id
            )
        )
    value = data[field]
    if not isinstance(value, str) or not value:
        raise ContentParseError(
            _format_error(
                f"Field '{field}' must be a non-empty string",
                source=source,
                event_id=event_id,
            )
        )
    return value


def _optional_str(
    value: Any,
    *,
    field: str,
    source: str,
    event_id: str,
) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ContentParseError(
            _format_error(
                f"Field '{field}' must be a string or null",
                source=source,
                event_id=event_id,
            )
        )
    return value


def _optional_condition(
    value: Any,
    *,
    field: str,
    source: str,
    event_id: str,
) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ContentParseError(
            _format_error(
                f"Field '{field}' must be an object or null",
                source=source,
                event_id=event_id,
            )
        )
    return dict(value)


def _parse_str_tuple(
    value: Any,
    *,
    field: str,
    source: str,
    event_id: str,
) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ContentParseError(
            _format_error(
                f"Field '{field}' must be a list of strings",
                source=source,
                event_id=event_id,
            )
        )
    return tuple(value)


def _parse_life_stage(value: Any, *, source: str, event_id: str) -> LifeStage | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ContentParseError(
            _format_error(
                "Field 'life_stage' must be a string or null",
                source=source,
                event_id=event_id,
            )
        )
    try:
        return LifeStage(value)
    except ValueError as exc:
        raise ContentParseError(
            _format_error(
                f"Unknown life_stage {value!r}",
                source=source,
                event_id=event_id,
            )
        ) from exc


def _parse_float(value: Any, *, field: str, source: str, event_id: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContentParseError(
            _format_error(
                f"Field '{field}' must be a number", source=source, event_id=event_id
            )
        )
    return float(value)


def _parse_int(value: Any, *, field: str, source: str, event_id: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContentParseError(
            _format_error(
                f"Field '{field}' must be an integer", source=source, event_id=event_id
            )
        )
    return value


def _format_error(message: str, *, source: str, event_id: str | None) -> str:
    if event_id:
        return f"{message} (file={source}, event_id={event_id})"
    return f"{message} (file={source})"
