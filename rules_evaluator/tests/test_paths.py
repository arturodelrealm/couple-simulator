from rules_evaluator import evaluate


def test_state_path(minimal_context: dict) -> None:
    rule = {
        "type": "compare",
        "path": "state/finances",
        "op": "gte",
        "value": 40,
    }
    assert evaluate(rule, minimal_context) is True

    low_finances = {
        **minimal_context,
        "state": {**minimal_context["state"], "finances": 30},
    }
    assert evaluate(rule, low_finances) is False


def test_missing_path_returns_false(minimal_context: dict) -> None:
    rule = {
        "type": "compare",
        "path": "state/missing_stat",
        "op": "gte",
        "value": 1,
    }
    assert evaluate(rule, minimal_context) is False


def test_nested_path(minimal_context: dict) -> None:
    rule = {
        "type": "compare",
        "path": "flags/mismatch_on_question/destination",
        "op": "eq",
        "value": True,
    }
    context = {
        **minimal_context,
        "flags": {
            **minimal_context["flags"],
            "mismatch_on_question": {"destination": True},
        },
    }
    assert evaluate(rule, context) is True


def test_event_variables_path(minimal_context: dict) -> None:
    rule = {
        "type": "compare",
        "path": "event_variables/home_desire",
        "op": "gte",
        "value": 4,
    }
    context = {
        **minimal_context,
        "event_variables": {"home_desire": 5},
    }
    assert evaluate(rule, context) is True


def test_answers_path(minimal_context: dict) -> None:
    rule = {
        "type": "compare",
        "path": "answers/want_dog",
        "op": "eq",
        "value": "yes",
    }
    context = {**minimal_context, "answers": {"want_dog": "yes"}}
    assert evaluate(rule, context) is True


def test_mode_path(minimal_context: dict) -> None:
    rule = {
        "type": "compare",
        "path": "mode",
        "op": "eq",
        "value": "couple",
    }
    assert evaluate(rule, minimal_context) is True


def test_tags_contains_path(minimal_context: dict) -> None:
    rule = {
        "type": "compare",
        "path": "tags",
        "op": "contains",
        "value": "financial",
    }
    assert evaluate(rule, minimal_context) is True
    assert evaluate(rule, {**minimal_context, "tags": []}) is False


def test_tags_dict_path(minimal_context: dict) -> None:
    rule = {
        "type": "compare",
        "path": "tags/financial",
        "op": "eq",
        "value": True,
    }
    context = {**minimal_context, "tags": {"financial": True}}
    assert evaluate(rule, context) is True


def test_list_index_path() -> None:
    rule = {
        "type": "compare",
        "path": "items/0/id",
        "op": "eq",
        "value": "first",
    }
    context = {"items": [{"id": "first"}, {"id": "second"}]}
    assert evaluate(rule, context) is True
