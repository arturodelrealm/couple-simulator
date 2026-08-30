from rules_evaluator import evaluate


def test_value_getter_compares_two_paths() -> None:
    rule = {
        "type": "compare",
        "path": "answers/partner_a/destination",
        "op": "eq",
        "value_getter": "answers/partner_b/destination",
    }
    matching = {
        "answers": {
            "partner_a": {"destination": "beach"},
            "partner_b": {"destination": "beach"},
        }
    }
    mismatch = {
        "answers": {
            "partner_a": {"destination": "beach"},
            "partner_b": {"destination": "mountain"},
        }
    }
    assert evaluate(rule, matching) is True
    assert evaluate(rule, mismatch) is False


def test_value_getter_with_ordering() -> None:
    rule = {
        "type": "compare",
        "path": "state/finances",
        "op": "gte",
        "value_getter": "thresholds/min_finances",
    }
    context = {
        "state": {"finances": 55},
        "thresholds": {"min_finances": 40},
    }
    assert evaluate(rule, context) is True

    low_context = {
        "state": {"finances": 30},
        "thresholds": {"min_finances": 40},
    }
    assert evaluate(rule, low_context) is False


def test_value_getter_with_contains() -> None:
    rule = {
        "type": "compare",
        "path": "tags",
        "op": "contains",
        "value_getter": "expected/primary_tag",
    }
    context = {
        "tags": ["financial", "housing"],
        "expected": {"primary_tag": "financial"},
    }
    assert evaluate(rule, context) is True


def test_literal_value_still_works(minimal_context: dict) -> None:
    rule = {
        "type": "compare",
        "path": "state/finances",
        "op": "gte",
        "value": 40,
    }
    assert evaluate(rule, minimal_context) is True
