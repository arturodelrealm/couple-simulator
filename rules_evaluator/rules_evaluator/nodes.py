"""Constants for condition node types and operators."""

TYPE_COMPARE = "compare"
TYPE_ALL = "all"
TYPE_ANY = "any"
TYPE_NOT = "not"

NODE_TYPES = frozenset({TYPE_COMPARE, TYPE_ALL, TYPE_ANY, TYPE_NOT})

OP_EQ = "eq"
OP_NEQ = "neq"
OP_GT = "gt"
OP_GTE = "gte"
OP_LT = "lt"
OP_LTE = "lte"
OP_IN = "in"
OP_CONTAINS = "contains"

OPERATORS = frozenset({OP_EQ, OP_NEQ, OP_GT, OP_GTE, OP_LT, OP_LTE, OP_IN, OP_CONTAINS})

MAX_TREE_DEPTH = 32
MAX_ITEMS_PER_NODE = 256
