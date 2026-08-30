# Plan de implementación: `rules_evaluator`

**Estado:** Borrador — listo para implementación  
**Ámbito:** Paquete Python independiente para evaluar `ConditionExpr` contra un contexto dict  
**Relacionado:** [game-event-content-model.md §5](./game-event-content-model.md), [game-engine-design.md](./game-engine-design.md), [couple-simulator-engine-package-skeleton.md](./couple-simulator-engine-package-skeleton.md)

---

## 1. Objetivo y alcance V1

### 1.1 Objetivo

Construir **`rules_evaluator/`** como paquete Python en la raíz del monorepo que evalúe expresiones de reglas (`ConditionExpr`) contra un **contexto JSON-serializable** (`dict`) y devuelva **`True` o `False`**.

El paquete es **agnóstico del dominio del juego**: no conoce `SimulationState`, FastAPI, SQLAlchemy ni el orquestador del engine. Solo interpreta el árbol de condiciones definido en [game-event-content-model.md §5](./game-event-content-model.md).

### 1.2 Alcance V1 (incluido)

| Capacidad | Detalle |
|-----------|---------|
| Nodos lógicos | `compare`, `all`, `any`, `not` |
| Targets | `state`, `event_var`, `answer`, `mode`, `tag`, `flag` |
| Operadores | `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `in` |
| API pública | `evaluate()`, `evaluate_all()` |
| Normalización legacy | Lista plana `[{...}, ...]` → `{"type": "all", "items": [...]}` |
| Vacíos | `None`, `{}`, `{"type": "all", "items": []}` → `True` |
| Tests | pytest sin DB, cobertura de operadores, targets y errores |
| Tooling | Ruff + pytest, `pip install -e "./rules_evaluator[dev]"` |

### 1.3 Fuera de alcance V1

- Outcomes, efectos, acciones, RNG, persistencia.
- Validación de contenido al cargar catálogos (responsabilidad futura del engine o del backend).
- Pydantic/dataclasses tipados para reglas (V1 trabaja con `dict` puro).
- Operadores o targets no documentados en §5.
- Librerías externas (JSON Logic, CEL, etc.).
- Integración del backend con el evaluador (el backend **no** importa `rules_evaluator` en V1).

### 1.4 Criterio de éxito V1

```bash
pip install -e "./rules_evaluator[dev]"
pytest rules_evaluator/tests/
```

- `evaluate(rule, context)` y `evaluate_all(rules, context)` producen resultados correctos en todos los tests.
- `couple_simulator_engine.conditions` puede delegar en `rules_evaluator` sin duplicar lógica.
- Cero dependencias de runtime aparte de la stdlib de Python ≥ 3.12.

---

## 2. Estructura del paquete en el monorepo

```text
couple-simulator/
├── backend/                         # NO importa rules_evaluator en V1
├── couple_simulator_engine/         # SÍ importa rules_evaluator (futuro)
├── rules_evaluator/                 # ← NUEVO
│   ├── pyproject.toml
│   ├── rules_evaluator/
│   │   ├── __init__.py              # API pública: evaluate, evaluate_all, excepciones
│   │   ├── api.py                   # evaluate(), evaluate_all(), normalize_rule()
│   │   ├── errors.py                # Jerarquía de excepciones
│   │   ├── nodes.py                 # Constantes de tipos de nodo y operadores
│   │   ├── normalize.py             # Legacy list → all; vacíos → None
│   │   ├── resolver.py              # Resolución de targets contra context
│   │   ├── operators.py             # Comparación tipada (eq, gt, in, …)
│   │   └── evaluator.py             # Visitor / recursión sobre el árbol
│   └── tests/
│       ├── conftest.py              # Fixtures: contextos mínimos reutilizables
│       ├── test_api.py              # evaluate / evaluate_all / vacíos
│       ├── test_normalize.py        # Legacy y reglas vacías
│       ├── test_compare.py          # Todos los operadores
│       ├── test_targets.py          # state, event_var, answer, mode, tag, flag
│       ├── test_composite.py        # all, any, not anidados
│       ├── test_errors.py           # Reglas inválidas
│       └── test_domain_examples.py  # Los 3 ejemplos del dominio (§9)
├── docs/specs/
│   └── rules-evaluator-implementation-plan.md   # este documento
└── Makefile                         # targets opcionales (fase 6)
```

### 2.1 `pyproject.toml` (alineado con `backend/`)

| Campo | Valor |
|-------|-------|
| `name` | `rules-evaluator` |
| `requires-python` | `>=3.12` |
| `dependencies` | ninguna |
| `optional-dependencies.dev` | `pytest>=8.0.0`, `ruff>=0.8.0` |
| `[tool.ruff]` | `line-length = 88`, `target-version = "py312"`, reglas `E`, `F`, `I` |
| `[tool.pytest.ini_options]` | `testpaths = ["tests"]`, `pythonpath = ["."]` |

Instalación en desarrollo desde la raíz del monorepo:

```bash
pip install -e "./rules_evaluator[dev]"
```

### 2.2 Nombre del paquete

Se mantiene **`rules_evaluator`** (directorio y módulo importable). No hay razón fuerte para renombrar: es descriptivo, coherente con el prompt y distinto de `couple_simulator_engine.conditions` (capa de adaptación del dominio).

---

## 3. API pública

### 3.1 Funciones

```python
def evaluate(rule: dict | list | None, context: dict) -> bool:
    """
    Evalúa una regla (o None) contra context.

    - None, dict vacío, o all con items vacío → True.
    - list → normaliza a {"type": "all", "items": list}.
  """

def evaluate_all(rules: list[dict | list | None], context: dict) -> bool:
    """
    Evalúa cada regla con evaluate(); devuelve True solo si todas pasan (AND implícito).
    Lista vacía → True.
    """
```

### 3.2 Contrato del `context`

El evaluador espera un `dict` con las claves documentadas en §5.3 de [game-event-content-model.md](./game-event-content-model.md). Claves **opcionales** con defaults seguros:

| Clave | Tipo esperado | Default si falta | Uso |
|-------|---------------|------------------|-----|
| `state` | `dict[str, Any]` | `{}` | Target `state` |
| `event_variables` | `dict[str, Any]` | `{}` | Target `event_var` |
| `answers` | `dict[str, str]` | `{}` | Target `answer` (`variable` = `question_id`) |
| `mode` | `str` | `None` | Target `mode` |
| `tags` | `list[str]` o `set[str]` | `[]` | Target `tag` |
| `flags` | `dict[str, Any]` | `{}` | Target `flag` |

**Nota:** El engine construirá este dict desde `EvaluationContext` (dataclass del dominio). El evaluador no importa tipos del engine.

### 3.3 Excepciones exportadas

```python
class RulesEvaluatorError(Exception):
    """Base del paquete."""

class InvalidRuleError(RulesEvaluatorError):
    """Estructura de regla inválida (tipo desconocido, campos faltantes, profundidad excesiva)."""

class UnknownOperatorError(InvalidRuleError):
    """Operador no soportado en nodo compare."""

class UnknownTargetError(InvalidRuleError):
    """Target no soportado en nodo compare."""

class InvalidContextError(RulesEvaluatorError):
    """Context con tipo incorrecto en una clave (p. ej. tags no es iterable)."""
```

**Política V1 — valor ausente vs regla inválida:**

| Situación | Comportamiento |
|-----------|----------------|
| Regla malformada (sin `type`, `op` inválido, `not` con ≠1 hijo) | `InvalidRuleError` |
| Variable inexistente en `state` / `event_variables` / `answers` / `flags` | `False` (condición no cumplida) |
| `context` no es `dict` | `TypeError` (error de programación del llamador) |
| `tags` presente pero no iterable | `InvalidContextError` |

Esta política favorece **elegibilidad conservadora**: un evento con condición sobre `finances` no entra al pool si el stat no está en el contexto, en lugar de fallar en runtime.

### 3.4 Exports en `__init__.py`

```python
from rules_evaluator.api import evaluate, evaluate_all
from rules_evaluator.errors import (
    InvalidContextError,
    InvalidRuleError,
    RulesEvaluatorError,
    UnknownOperatorError,
    UnknownTargetError,
)

__all__ = [
    "evaluate",
    "evaluate_all",
    "RulesEvaluatorError",
    "InvalidRuleError",
    "UnknownOperatorError",
    "UnknownTargetError",
    "InvalidContextError",
]
```

---

## 4. Diseño interno

### 4.1 Flujo de evaluación

```text
evaluate(rule, context)
  │
  ├─ normalize_rule(rule)          → dict | None
  ├─ si None o vacío efectivo      → True
  └─ _evaluate_node(node, context)
        │
        ├─ type == "compare"  → resolver.resolve_compare(node, context)
        ├─ type == "all"      → all(_evaluate_node(child) for child in items)
        ├─ type == "any"      → any(...)
        ├─ type == "not"      → not _evaluate_node(items[0])
        └─ otro               → InvalidRuleError
```

### 4.2 Normalización (`normalize.py`)

1. `None` → `None`
2. `list` → `{"type": "all", "items": [normalize_rule(item) for item in list]}`
3. `dict` sin `type` pero con claves de compare (`target`, `op`, …) → se trata como nodo `compare` si tiene `type: "compare"` implícito **no**; solo listas planas son legacy. Un dict sin `type` → `InvalidRuleError`.
4. `{"type": "all", "items": []}` → `None` (evalúa a `True`)

### 4.3 Resolución de targets (`resolver.py`)

| `target` | Resolución | `variable` | `value` en compare |
|----------|------------|------------|-------------------|
| `state` | `context["state"].get(variable)` | nombre del stat | literal a comparar |
| `event_var` | `context["event_variables"].get(variable)` | nombre de variable temporal | literal |
| `answer` | `context["answers"].get(variable)` | `question_id` | `option_id` esperado |
| `mode` | `context.get("mode")` | ignorado en V1 | modo esperado (`"solo"` / `"couple"`) |
| `tag` | N/A (no usa variable) | ignorado | tag a buscar en `context["tags"]` |
| `flag` | ver §4.4 | nombre del flag | literal |

Para `tag`, la semántica es: **`value in tags`** — equivalente a un compare donde el operando izquierdo es la pertenencia al conjunto de tags del evento. Se implementa soportando `op: "eq"` con `value: true` como alias de presencia, y también `op: "in"` invertido; la forma canónica del contenido es:

```json
{"type": "compare", "target": "tag", "variable": "", "op": "eq", "value": "financial"}
```

→ `True` si `"financial"` está en `tags`. El campo `variable` se ignora.

### 4.4 Semántica de flags

| `variable` | Lectura en `context["flags"]` | Ejemplo |
|------------|----------------------------------|---------|
| `answers_match` | bool | `eq` / `true` |
| `has_mismatch` | bool | `eq` / `true` |
| `mismatch_on_question` | bool por `question_id` | `variable` en el nodo = `question_id` del flag; `value` = mismo id confirma mismatch en esa pregunta |

Convención para `mismatch_on_question`: el engine poblará `flags` como:

```python
flags = {
    "answers_match": False,
    "has_mismatch": True,
    "mismatch_on_question": {
        "destination": True,
        "budget": False,
    },
}
```

El resolver para `target: "flag"`, `variable: "mismatch_on_question"` lee `flags["mismatch_on_question"].get(value, False)` cuando `op` es `eq` y `value` es el `question_id`. Para `has_mismatch` y `answers_match`, lee `flags.get(variable)`.

> **Delta respecto al spec:** [game-event-content-model.md §5.3](./game-event-content-model.md) menciona `mismatch_on_question` con `variable = question_id` en la tabla de flags, pero el ejemplo en §8.5 usa `"variable": "mismatch_on_question", "value": "destination"`. El plan adopta el **ejemplo §8.5** (variable fija `mismatch_on_question`, value = question_id) por ser más explícito y extensible. Ver §11.

### 4.5 Operadores (`operators.py`)

| `op` | Semántica | Notas |
|------|-----------|-------|
| `eq` | `left == right` | |
| `neq` | `left != right` | |
| `gt` | `left > right` | Requiere tipos comparables; si no → `False` |
| `gte` | `left >= right` | |
| `lt` | `left < right` | |
| `lte` | `left <= right` | |
| `in` | `left in right` | `right` debe ser iterable; si no → `False` |

**Coerción V1:** ninguna. `5` ≠ `"5"`. El contenido y el engine deben usar tipos consistentes.

**Comparación con `None`:** si el operando izquierdo es `None` (variable ausente), el resultado es `False` para todos los operadores excepto `eq`/`neq` con `right is None`.

### 4.6 Límites defensivos

- Profundidad máxima del árbol: **32 niveles** (configurable constante). Exceder → `InvalidRuleError`.
- Tamaño máximo de `items` en `all`/`any`: **256** (configurable). Evita reglas accidentalmente enormes.

### 4.7 Sin visitor orientado a objetos en V1

V1 usa **recursión sobre dict** en `evaluator.py` (funciones puras). Si en el futuro se añaden validación estática o optimización, se puede introducir un visitor sin cambiar la API pública.

---

## 5. Manejo de errores

### 5.1 Matriz de errores

| Caso | Excepción / resultado |
|------|----------------------|
| `type` ausente o desconocido | `InvalidRuleError` |
| `compare` sin `target`, `op` o `value` (salvo `mode`/`tag` donde `variable` es opcional) | `InvalidRuleError` |
| `all`/`any` sin `items` o `items` no es lista | `InvalidRuleError` |
| `not` con 0 o >1 items | `InvalidRuleError` |
| `op` no reconocido | `UnknownOperatorError` |
| `target` no reconocido | `UnknownTargetError` |
| Variable ausente en contexto | `False` |
| `left` y `right` incomparables en orden total | `False` |

### 5.2 Mensajes de error

Mensajes en **inglés** (convención del repo), con ruta en el árbol para depuración:

```text
InvalidRuleError: unknown node type 'xor' at root
UnknownOperatorError: unsupported operator 'contains' in compare node
UnknownTargetError: unsupported target 'player' in compare node
```

Opcional V1.1: campo `path: tuple[str, ...]` en la excepción (`("items", "0", "items", "1")`).

---

## 6. Plan por fases

### Fase 0 — Scaffolding (S)

| ID | Tarea | Done cuando |
|----|-------|-------------|
| 0.1 | Crear `rules_evaluator/pyproject.toml` y estructura de directorios | `pip install -e "./rules_evaluator[dev]"` exitoso |
| 0.2 | `errors.py` con jerarquía de excepciones | Importable desde `rules_evaluator` |
| 0.3 | `nodes.py` con constantes (`TYPE_COMPARE`, `OP_GTE`, …) | Usado por tests y evaluator |
| 0.4 | `tests/conftest.py` con `minimal_context` fixture | pytest recoge el paquete |

### Fase 1 — Normalización y API vacía (S)

| ID | Tarea | Done cuando |
|----|-------|-------------|
| 1.1 | `normalize.py`: None, list legacy, all vacío | `test_normalize.py` verde |
| 1.2 | `api.py`: `evaluate` / `evaluate_all` con stub que solo normaliza | `test_api.py` para vacíos |

### Fase 2 — Nodo `compare` y operadores (M)

| ID | Tarea | Done cuando |
|----|-------|-------------|
| 2.1 | `operators.py` con los 7 operadores | `test_compare.py` unitario |
| 2.2 | `resolver.py` para targets `state`, `event_var`, `answer` | `test_targets.py` parcial |
| 2.3 | `evaluator.py` — solo hojas `compare` | Integración en `evaluate()` |

### Fase 3 — Nodos compuestos (S)

| ID | Tarea | Done cuando |
|----|-------|-------------|
| 3.1 | `all`, `any`, `not` en `evaluator.py` | `test_composite.py` |
| 3.2 | Límite de profundidad y validación de `items` | `test_errors.py` |

### Fase 4 — Targets restantes (M)

| ID | Tarea | Done cuando |
|----|-------|-------------|
| 4.1 | Target `mode` | Tests con `solo` / `couple` |
| 4.2 | Target `tag` | Tests de presencia/ausencia de tag |
| 4.3 | Target `flag` (`answers_match`, `has_mismatch`, `mismatch_on_question`) | Tests alineados con §8.5 del content model |

### Fase 5 — Ejemplos de dominio y endurecimiento (M)

| ID | Tarea | Done cuando |
|----|-------|-------------|
| 5.1 | `test_domain_examples.py` con los 3 escenarios (§9) | Verde |
| 5.2 | Revisión de mensajes de error y casos límite (`None`, tipos mixtos) | `test_errors.py` completo |
| 5.3 | Documentación en docstrings de `api.py` | Sphinx/no requerido; docstrings suficientes |

### Fase 6 — Integración monorepo (S)

| ID | Tarea | Done cuando |
|----|-------|-------------|
| 6.1 | Añadir targets Makefile: `lint-rules-evaluator`, `test-rules-evaluator` | `make test-rules-evaluator` funciona |
| 6.2 | (Opcional) Entrada en `.pre-commit-config.yaml` para Ruff en `rules_evaluator/` | Hook pasa |
| 6.3 | Cuando exista `couple_simulator_engine/`: dependencia editable y `conditions.py` delegando | `test_conditions.py` del engine pasa sin duplicar lógica |

**Orden recomendado:** 0 → 1 → 2 → 3 → 4 → 5 → 6. Las fases 2 y 3 pueden solaparse si hay dos contribuidores; la 6.3 depende del scaffold del engine (fase 3 del [skeleton §10](./couple-simulator-engine-package-skeleton.md)).

**Estimación total:** ~2–3 días de implementación enfocada para V1 completa.

---

## 7. Estrategia de tests

### 7.1 Principios

- Sin base de datos ni red.
- Tabla de casos por operador (parametrized pytest).
- Fixtures de contexto mínimo en `conftest.py`.
- Los tests del evaluador **no** importan `couple_simulator_engine`.

### 7.2 Fixture base

```python
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
```

### 7.3 Casos concretos por categoría

**Vacíos y legacy**

- `evaluate(None, ctx)` → `True`
- `evaluate({"type": "all", "items": []}, ctx)` → `True`
- `evaluate([cond1, cond2], ctx)` equivalente a `all` implícito

**Operadores** (parametrizado, left/right explícitos)

- `eq`: `40 == 40` → True; `40 == 41` → False
- `gte` / `lt`: bordes numéricos
- `in`: `"beach" in ["beach", "mountain"]` → True
- Comparación incomparable (`gt` con str y int) → False

**Targets**

- `state.finances gte 40` con finances=55 → True; con finances=30 → False
- `event_var.home_desire gte 4` tras acumular efectos
- `answer.want_dog eq yes` con answers `{"want_dog": "yes"}`
- `mode eq couple`
- `tag eq financial` con tags del evento
- `flag.has_mismatch eq true` con flags poblados por ConflictResolver

**Compuestos**

- Árbol del ejemplo §5.1 del content model (any → all → compares)
- `not` sobre compare simple
- Anidación 4+ niveles

**Errores**

- `type: "xor"` → `InvalidRuleError`
- `op: "contains"` → `UnknownOperatorError`
- `not` sin items → `InvalidRuleError`

---

## 8. Integración con `couple_simulator_engine/conditions.py`

### 8.1 División de responsabilidades

| Capa | Paquete | Responsabilidad |
|------|---------|-----------------|
| Evaluación genérica | `rules_evaluator` | Árbol `ConditionExpr` + `dict` context → `bool` |
| Adaptación de dominio | `couple_simulator_engine.conditions` | `EvaluationContext` → dict; API tipada para el engine |

### 8.2 Dependencia en `couple_simulator_engine/pyproject.toml`

```toml
[project]
dependencies = [
    "rules-evaluator",
]

[tool.setuptools.dynamic]  # o path editable en dev
```

Desarrollo local (monorepo):

```toml
# couple_simulator_engine/pyproject.toml
dependencies = [
    "rules-evaluator @ file:///${PROJECT_ROOT}/rules_evaluator",
]
```

O instalación conjunta:

```bash
pip install -e "./rules_evaluator[dev]" -e "./couple_simulator_engine[dev]"
```

### 8.3 Implementación prevista de `conditions.py`

```python
# couple_simulator_engine/conditions.py (futuro — no parte de rules_evaluator V1)

from dataclasses import dataclass
from typing import Any

from rules_evaluator import evaluate as _evaluate

@dataclass
class EvaluationContext:
    state: Any  # SimulationState o dict
    event_variables: dict[str, Any]
    answers: dict[str, str]
    answers_by_player: dict[str, dict[str, str]]  # no usado por el evaluador V1
    mode: str
    tags: frozenset[str]
    flags: dict[str, Any]

def _context_to_dict(ctx: EvaluationContext) -> dict:
    state = ctx.state
    if hasattr(state, "__dataclass_fields__"):
        from dataclasses import asdict
        state = asdict(state)
    return {
        "state": state,
        "event_variables": ctx.event_variables,
        "answers": ctx.answers,
        "mode": ctx.mode,
        "tags": list(ctx.tags),
        "flags": ctx.flags,
    }

def evaluate(expr: dict | list | None, ctx: EvaluationContext) -> bool:
    return _evaluate(expr, _context_to_dict(ctx))

def evaluate_all(exprs: list[dict | list | None], ctx: EvaluationContext) -> bool:
    from rules_evaluator import evaluate_all as _evaluate_all
    return _evaluate_all(exprs, _context_to_dict(ctx))
```

### 8.4 Puntos de uso en el engine

| Módulo del engine | Uso del evaluador |
|-------------------|-------------------|
| `selection/event_selector.py` | `event.eligibility` contra state + tags + mode |
| `resolution/outcomes.py` | Cada `outcome.when` (varios pueden aplicar) |
| `engine.py` (futuro V2) | `question.show_when` al presentar evento |
| `resolution/conflict.py` | Puebla `flags` antes de evaluar outcomes de mismatch |

### 8.5 Tests del engine

`couple_simulator_engine/tests/test_conditions.py` debe contener **smoke tests de integración** (contexto de dominio → bool), no reimplementar la matriz de operadores (eso vive en `rules_evaluator/tests/`).

---

## 9. Ejemplos de reglas del dominio

### 9.1 Elegibilidad — comprar casa (finanzas y edad)

Evento entra al pool solo si las finanzas son suficientes **y** la edad ≥ 25.

```json
{
  "type": "all",
  "items": [
    {"type": "compare", "target": "state", "variable": "finances", "op": "gte", "value": 40},
    {"type": "compare", "target": "state", "variable": "age", "op": "gte", "value": 25}
  ]
}
```

**Contexto de prueba:**

```python
context = {
    "state": {"finances": 55, "age": 30},
    "event_variables": {},
    "answers": {},
    "mode": "couple",
    "tags": ["financial", "housing"],
    "flags": {},
}
# evaluate(rule, context) → True
```

### 9.2 Outcome — compra exitosa (señales acumuladas)

Tras responder las preguntas, `home_desire` y `home_budget` determinan el outcome «purchase».

```json
{
  "type": "all",
  "items": [
    {"type": "compare", "target": "event_var", "variable": "home_desire", "op": "gte", "value": 4},
    {"type": "compare", "target": "event_var", "variable": "home_budget", "op": "gte", "value": 2}
  ]
}
```

**Contexto tras efectos de opciones:**

```python
context = {
    "state": {"finances": 55, "age": 30},
    "event_variables": {"home_desire": 5, "home_budget": 2},
    "answers": {"want_to_buy": "yes", "budget_ready": "yes"},
    "mode": "couple",
    "tags": [],
    "flags": {"has_mismatch": False},
}
# evaluate(rule, context) → True
```

### 9.3 Mismatch — vacaciones (playa vs montaña)

Outcome específico cuando hubo desacuerdo en la pregunta `destination`.

```json
{
  "type": "compare",
  "target": "flag",
  "variable": "mismatch_on_question",
  "op": "eq",
  "value": "destination"
}
```

**Contexto tras ConflictResolver:**

```python
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
# evaluate(rule, context) → True
```

Combinación con tag para narrativa solo en eventos de preferencia:

```json
{
  "type": "all",
  "items": [
    {"type": "compare", "target": "flag", "variable": "has_mismatch", "op": "eq", "value": true},
    {"type": "compare", "target": "tag", "variable": "", "op": "eq", "value": "preference"}
  ]
}
```

---

## 10. Riesgos y decisiones abiertas

### 10.1 Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Divergencia entre specs (`list[Condition]` en [game-engine-design.md](./game-engine-design.md) vs `ConditionExpr` en content model) | El evaluador implementa **solo** `ConditionExpr`. Actualizar game-engine-design en una tarea aparte. |
| Semántica ambigua de `mismatch_on_question` | Adoptar forma §8.5; documentar en content model si hace falta |
| Tipos inconsistentes en JSON de contenido (`40` vs `"40"`) | Sin coerción en V1; validación al cargar contenido (futuro) |
| Duplicación de tests entre paquetes | Matriz completa en `rules_evaluator`; smoke en engine |
| `game-event-content-model.md` §5.1 dice que el evaluador vive en `couple_simulator_engine` | Refactor documental: el **motor genérico** vive en `rules_evaluator`; el engine solo adapta contexto |

### 10.2 Decisiones abiertas (resolver antes o durante implementación)

| ID | Pregunta | Propuesta V1 | Alternativa |
|----|----------|--------------|-------------|
| D1 | ¿`tag` usa `variable` o solo `value`? | Solo `value` = tag | `variable` = tag, sin `value` |
| D2 | ¿Variable ausente → False o error? | **False** | `InvalidContextError` en modo strict |
| D3 | ¿Exportar `normalize_rule()` públicamente? | No (interno) | Sí, para validadores de contenido |
| D4 | ¿Soporte `answers_by_player` en el evaluador? | No en V1; el engine resuelve respuestas efectivas antes | Targets `answer_a` / `answer_b` |
| D5 | ¿Makefile targets dedicados? | Sí (`test-rules-evaluator`, `lint-rules-evaluator`) | Solo documentar pip/pytest manual |

### 10.3 Delta documental propuesto (content model)

**§5.1 — Ubicación del evaluador:** cambiar «el paquete `couple_simulator_engine` implementa un evaluador propio» por «el paquete `rules_evaluator` implementa el evaluador; `couple_simulator_engine.conditions` lo consume».

**§5.3 — Flags `mismatch_on_question`:** unificar la tabla con el ejemplo §8.5 (`variable: "mismatch_on_question"`, `value: <question_id>`).

No se requieren cambios en la forma JSON de `ConditionExpr`.

---

## 11. Referencias y trazabilidad

| Documento | Relación con este plan |
|-----------|------------------------|
| [game-event-content-model.md §5](./game-event-content-model.md) | **Fuente de verdad** para `ConditionExpr`, targets y operadores |
| [game-event-content-model.md §8.5, §11, §12](./game-event-content-model.md) | Ejemplos de mismatch, flujo y compra de casa |
| [game-engine-design.md](./game-engine-design.md) | Usos del evaluador (elegibilidad, outcomes); actualizar modelo `Condition` → `ConditionExpr` |
| [couple-simulator-engine-package-skeleton.md §4.1, §8, §10](./couple-simulator-engine-package-skeleton.md) | `conditions.py` delega en `rules_evaluator`; orden de implementación |
| [AGENTS.md](../../AGENTS.md) | Python ≥ 3.12, inglés en código, Ruff, pytest, sin DB |
| [rules-evaluator-implementation-plan-prompt.md](./rules-evaluator-implementation-plan-prompt.md) | Prompt que originó este plan |

---

## 12. Checklist post-implementación

- [ ] `pip install -e "./rules_evaluator[dev]"` desde la raíz
- [ ] `pytest rules_evaluator/tests/` — todos verdes
- [ ] `ruff check rules_evaluator/` y `ruff format --check rules_evaluator/`
- [ ] `evaluate()` / `evaluate_all()` exportados en `rules_evaluator/__init__.py`
- [ ] Tests de los 3 ejemplos de dominio (§9)
- [ ] `couple_simulator_engine` depende de `rules-evaluator` y `conditions.py` delega (cuando exista el engine)
- [ ] (Opcional) `make test-rules-evaluator` en Makefile
- [ ] Delta documental en game-event-content-model §5.1 aplicado o ticket creado
