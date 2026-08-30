"""Exception hierarchy for the rules evaluator."""


class RulesEvaluatorError(Exception):
    """Base exception for the rules evaluator package."""


class InvalidRuleError(RulesEvaluatorError):
    """Raised when a rule has an invalid structure."""


class UnknownOperatorError(InvalidRuleError):
    """Raised when a compare node uses an unsupported operator."""


class InvalidContextError(RulesEvaluatorError):
    """Raised when the evaluation context has an invalid shape."""
