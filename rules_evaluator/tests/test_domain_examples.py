from rules_evaluator import evaluate


def test_house_eligibility() -> None:
    rule = {
        "type": "all",
        "items": [
            {
                "type": "compare",
                "path": "state/finances",
                "op": "gte",
                "value": 40,
            },
            {
                "type": "compare",
                "path": "state/age",
                "op": "gte",
                "value": 25,
            },
        ],
    }
    context = {
        "state": {"finances": 55, "age": 30},
        "event_variables": {},
        "answers": {},
        "mode": "couple",
        "tags": ["financial", "housing"],
        "flags": {},
    }
    assert evaluate(rule, context) is True


def test_house_purchase_outcome() -> None:
    rule = {
        "type": "all",
        "items": [
            {
                "type": "compare",
                "path": "event_variables/home_desire",
                "op": "gte",
                "value": 4,
            },
            {
                "type": "compare",
                "path": "event_variables/home_budget",
                "op": "gte",
                "value": 2,
            },
        ],
    }
    context = {
        "state": {"finances": 55, "age": 30},
        "event_variables": {"home_desire": 5, "home_budget": 2},
        "answers": {"want_to_buy": "yes", "budget_ready": "yes"},
        "mode": "couple",
        "tags": [],
        "flags": {"has_mismatch": False},
    }
    assert evaluate(rule, context) is True


def test_vacation_mismatch_outcome() -> None:
    rule = {
        "type": "compare",
        "path": "flags/mismatch_on_question/destination",
        "op": "eq",
        "value": True,
    }
    context = {
        "state": {"compatibility": 75},
        "event_variables": {},
        "answers": {"destination": "beach"},
        "mode": "couple",
        "tags": ["preference"],
        "flags": {
            "answers_match": False,
            "has_mismatch": True,
            "mismatch_on_question": {"destination": True},
        },
    }
    assert evaluate(rule, context) is True


def test_vacation_mismatch_with_preference_tag() -> None:
    rule = {
        "type": "all",
        "items": [
            {
                "type": "compare",
                "path": "flags/has_mismatch",
                "op": "eq",
                "value": True,
            },
            {
                "type": "compare",
                "path": "tags",
                "op": "contains",
                "value": "preference",
            },
        ],
    }
    context = {
        "state": {"compatibility": 75},
        "event_variables": {},
        "answers": {},
        "mode": "couple",
        "tags": ["preference"],
        "flags": {"has_mismatch": True},
    }
    assert evaluate(rule, context) is True
