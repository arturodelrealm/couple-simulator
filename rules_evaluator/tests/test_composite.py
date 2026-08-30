from rules_evaluator import evaluate


def test_all_node(minimal_context: dict) -> None:
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
    assert evaluate(rule, minimal_context) is True


def test_any_node(minimal_context: dict) -> None:
    rule = {
        "type": "any",
        "items": [
            {
                "type": "compare",
                "path": "state/finances",
                "op": "gte",
                "value": 100,
            },
            {
                "type": "compare",
                "path": "state/age",
                "op": "gte",
                "value": 25,
            },
        ],
    }
    assert evaluate(rule, minimal_context) is True


def test_not_node(minimal_context: dict) -> None:
    rule = {
        "type": "not",
        "items": [
            {
                "type": "compare",
                "path": "state/finances",
                "op": "lt",
                "value": 10,
            }
        ],
    }
    assert evaluate(rule, minimal_context) is True


def test_nested_tree_from_spec(minimal_context: dict) -> None:
    rule = {
        "type": "any",
        "items": [
            {
                "type": "all",
                "items": [
                    {
                        "type": "compare",
                        "path": "state/finances",
                        "op": "gte",
                        "value": 60,
                    },
                    {
                        "type": "compare",
                        "path": "state/children",
                        "op": "gte",
                        "value": 1,
                    },
                ],
            },
            {
                "type": "compare",
                "path": "event_variables/home_desire",
                "op": "gte",
                "value": 4,
            },
        ],
    }
    assert evaluate(rule, minimal_context) is False

    context = {
        **minimal_context,
        "event_variables": {"home_desire": 4},
    }
    assert evaluate(rule, context) is True


def test_flat_list_as_implicit_all(minimal_context: dict) -> None:
    rules = [
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
    ]
    assert evaluate(rules, minimal_context) is True
