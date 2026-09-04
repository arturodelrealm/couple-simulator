"""Tests for JSON event loading and ContentCatalog."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from couple_simulator_engine.content.catalog import ContentCatalog, load_catalog
from couple_simulator_engine.content.loader import (
    ContentParseError,
    DuplicateEventIdError,
    load_event_file,
)


def _write_event(directory: Path, filename: str, payload: dict) -> Path:
    path = directory / filename
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _minimal_event(**overrides: object) -> dict:
    data: dict = {
        "id": "minimal",
        "title": "Minimal event",
        "questions": [
            {
                "id": "q1",
                "text": "Choose",
                "options": [
                    {"id": "a", "text": "A"},
                    {"id": "b", "text": "B", "actions": []},
                ],
            }
        ],
    }
    data.update(overrides)
    return data


def test_load_catalog_returns_one_event_per_json_file(tmp_path: Path) -> None:
    _write_event(tmp_path, "one.json", _minimal_event(id="one", title="One"))
    _write_event(tmp_path, "two.json", _minimal_event(id="two", title="Two"))
    (tmp_path / "ignored.txt").write_text("not json", encoding="utf-8")

    catalog = load_catalog(tmp_path)
    events = catalog.all_events()

    assert len(events) == 2
    assert {event.id for event in events} == {"one", "two"}
    assert catalog.get("one") is not None
    assert catalog.get("unknown") is None


def test_duplicate_event_id_raises(tmp_path: Path) -> None:
    _write_event(tmp_path, "a.json", _minimal_event(id="dup", title="A"))
    _write_event(tmp_path, "b.json", _minimal_event(id="dup", title="B"))

    with pytest.raises(DuplicateEventIdError, match="Duplicate event id 'dup'"):
        load_catalog(tmp_path)


def test_invalid_json_raises_with_file_context(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(ContentParseError, match="Invalid JSON") as exc_info:
        load_event_file(path)
    assert "bad.json" in str(exc_info.value)


def test_missing_required_fields_raise_with_event_context(tmp_path: Path) -> None:
    path = _write_event(tmp_path, "no_title.json", {"id": "no_title", "questions": []})

    with pytest.raises(
        ContentParseError, match="Missing required field 'title'"
    ) as exc:
        load_event_file(path)
    assert "event_id=no_title" in str(exc.value)
    assert "no_title.json" in str(exc.value)

    missing_id = _write_event(tmp_path, "no_id.json", {"title": "X", "questions": []})
    with pytest.raises(ContentParseError, match="Missing required field 'id'"):
        load_event_file(missing_id)

    missing_questions = _write_event(
        tmp_path, "no_questions.json", {"id": "nq", "title": "X"}
    )
    with pytest.raises(ContentParseError, match="Missing required field 'questions'"):
        load_event_file(missing_questions)


def test_question_requires_at_least_one_option(tmp_path: Path) -> None:
    payload = _minimal_event()
    payload["questions"][0]["options"] = []
    path = _write_event(tmp_path, "empty_opts.json", payload)

    with pytest.raises(ContentParseError, match="at least one option"):
        load_event_file(path)


def test_optional_fields_use_spec_defaults(tmp_path: Path) -> None:
    path = _write_event(
        tmp_path,
        "defaults.json",
        {
            "id": "defaults",
            "title": "Defaults",
            "eligibility": None,
            "questions": [
                {
                    "id": "q1",
                    "text": "Q",
                    "options": [{"id": "a", "text": "A"}],
                }
            ],
        },
    )
    event = load_event_file(path)

    assert event.description is None
    assert event.tags == ()
    assert event.life_stage is None
    assert event.eligibility is None
    assert event.outcomes == ()
    assert event.default_actions == ()
    assert event.mismatch_actions == ()
    assert event.weight == 1.0
    assert event.weight_rules == ()
    assert event.max_occurrences == 1
    assert event.player_role is None
    assert event.use_answer_bank is True
    assert event.questions[0].options[0].actions == ()


def test_weight_rules_parsed(tmp_path: Path) -> None:
    payload = _minimal_event(
        weight=1.0,
        weight_rules=[
            {
                "when": {
                    "type": "compare",
                    "path": "state/compatibility",
                    "op": "lt",
                    "value": 20,
                },
                "weight": 2.0,
            }
        ],
    )
    event = load_event_file(_write_event(tmp_path, "weighted.json", payload))

    assert event.weight == 1.0
    assert len(event.weight_rules) == 1
    assert event.weight_rules[0].weight == 2.0
    assert event.weight_rules[0].when is not None
    assert event.weight_rules[0].when["path"] == "state/compatibility"


def test_weight_rule_missing_weight_raises(tmp_path: Path) -> None:
    payload = _minimal_event(
        weight_rules=[
            {
                "when": {
                    "type": "compare",
                    "path": "state/age",
                    "op": "gt",
                    "value": 0,
                }
            }
        ],
    )
    with pytest.raises(ContentParseError, match="requires field 'weight'"):
        load_event_file(_write_event(tmp_path, "bad_weight_rule.json", payload))


def test_eligibility_and_when_null_stored_as_none(tmp_path: Path) -> None:
    payload = _minimal_event(
        eligibility=None,
        outcomes=[{"id": "always", "when": None, "actions": []}],
        questions=[
            {
                "id": "q1",
                "text": "Q",
                "options": [
                    {
                        "id": "a",
                        "text": "A",
                        "actions": [
                            {
                                "type": "modify_stat",
                                "args": {"variable": "quality_of_life", "delta": 1},
                            }
                        ],
                    }
                ],
            }
        ],
    )
    event = load_event_file(_write_event(tmp_path, "nulls.json", payload))

    assert event.eligibility is None
    assert event.outcomes[0].when is None
    assert event.questions[0].options[0].actions[0].when is None


def test_content_catalog_get_unknown_id() -> None:
    catalog = ContentCatalog()
    assert catalog.get("missing") is None
    assert catalog.all_events() == ()


# --- TextPresentation loader tests ---

from couple_simulator_engine.content.definitions import TextPresentation  # noqa: E402


def test_load_event_with_text_presentation_on_question_and_option(
    tmp_path: Path,
) -> None:
    payload = {
        "id": "tp_event",
        "title": "TP event",
        "questions": [
            {
                "id": "q1",
                "text": {
                    "default_key": "events.tp.q1.default",
                    "by_sex": {
                        "male": "events.tp.q1.male",
                        "female": "events.tp.q1.female",
                    },
                },
                "options": [
                    {
                        "id": "a",
                        "text": {
                            "default_key": "events.tp.opt_a.default",
                            "by_role": {
                                "partner_a": "events.tp.opt_a.role_a",
                                "partner_b": "events.tp.opt_a.role_b",
                            },
                        },
                    },
                    {"id": "b", "text": "events.tp.opt_b.plain"},
                ],
            }
        ],
    }
    event = load_event_file(_write_event(tmp_path, "tp.json", payload))
    assert isinstance(event.questions[0].text, TextPresentation)
    assert event.questions[0].text.default_key == "events.tp.q1.default"
    assert event.questions[0].text.by_sex == {
        "male": "events.tp.q1.male",
        "female": "events.tp.q1.female",
    }
    opt_a = event.questions[0].options[0]
    assert isinstance(opt_a.text, TextPresentation)
    assert opt_a.text.by_role == {
        "partner_a": "events.tp.opt_a.role_a",
        "partner_b": "events.tp.opt_a.role_b",
    }
    opt_b = event.questions[0].options[1]
    assert isinstance(opt_b.text, str)
    assert opt_b.text == "events.tp.opt_b.plain"


def test_text_presentation_missing_default_key_raises(tmp_path: Path) -> None:
    payload = {
        "id": "bad_tp",
        "title": "Bad",
        "questions": [
            {
                "id": "q1",
                "text": {"by_sex": {"male": "m"}},
                "options": [{"id": "a", "text": "A"}],
            }
        ],
    }
    with pytest.raises(ContentParseError, match="default_key"):
        load_event_file(_write_event(tmp_path, "bad_tp.json", payload))


def test_text_presentation_non_string_variant_values_raises(tmp_path: Path) -> None:
    payload = {
        "id": "bad_var",
        "title": "Bad",
        "questions": [
            {
                "id": "q1",
                "text": {
                    "default_key": "ok",
                    "by_sex": {"male": 123},
                },
                "options": [{"id": "a", "text": "A"}],
            }
        ],
    }
    with pytest.raises(ContentParseError, match="string keys and values"):
        load_event_file(_write_event(tmp_path, "bad_var.json", payload))


def test_text_field_rejects_non_string_non_object(tmp_path: Path) -> None:
    payload = {
        "id": "bad_type",
        "title": "Bad",
        "questions": [
            {
                "id": "q1",
                "text": 42,
                "options": [{"id": "a", "text": "A"}],
            }
        ],
    }
    with pytest.raises(ContentParseError, match="string or TextPresentation"):
        load_event_file(_write_event(tmp_path, "bad_type.json", payload))


def test_player_role_and_use_answer_bank_fields(tmp_path: Path) -> None:
    path = _write_event(
        tmp_path,
        "b_only.json",
        _minimal_event(player_role="partner_b", use_answer_bank=False),
    )
    event = load_event_file(path)
    assert event.player_role is not None
    assert event.player_role.value == "partner_b"
    assert event.use_answer_bank is False


def test_unknown_player_role_raises(tmp_path: Path) -> None:
    path = _write_event(tmp_path, "bad_role.json", _minimal_event(player_role="npc"))
    with pytest.raises(ContentParseError, match="Unknown player_role"):
        load_event_file(path)
