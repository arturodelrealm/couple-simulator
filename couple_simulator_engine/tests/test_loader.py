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
    assert event.max_occurrences == 1
    assert event.questions[0].options[0].actions == ()


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
                                "args": {"variable": "career", "delta": 1},
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
