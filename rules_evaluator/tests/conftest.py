import pytest


@pytest.fixture
def minimal_context() -> dict:
    return {
        "state": {
            "age": 30,
            "finances": 55,
            "compatibility": 80,
            "children": 0,
        },
        "event_variables": {},
        "answers": {},
        "mode": "couple",
        "tags": ["financial"],
        "flags": {
            "answers_match": True,
            "has_mismatch": False,
            "mismatch_on_question": {},
        },
    }
