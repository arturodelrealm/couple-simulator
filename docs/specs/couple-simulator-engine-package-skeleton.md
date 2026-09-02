# Esqueleto del paquete `couple_simulator_engine`

**Estado:** Borrador — guía de implementación
**Ámbito:** Estructura de directorios, módulos y responsabilidades del paquete Python
**Relacionado:** [game-engine-design.md](./game-engine-design.md)

---

## 1. Propósito

Este documento describe **cómo organizar el código** del game engine como paquete Python independiente. No contiene implementación; define el mapa de módulos, qué va en cada uno y qué exporta la API pública.

El paquete vive en la raíz del monorepo, **sin depender** de FastAPI, SQLAlchemy ni del backend.

---

## 2. Árbol de directorios

```text
couple-simulator/
├── couple_simulator_engine/
│   ├── pyproject.toml
│   ├── couple_simulator_engine/
│   │   ├── __init__.py              # API pública
│   │   ├── engine.py                # GameEngine — orquestador
│   │   ├── config.py                # GameConfig
│   │   ├── session.py               # Match, SimulationRun, LoadedGame, DTOs de sesión
│   │   ├── snapshot.py              # GameSnapshot — hidratación desde persistencia
│   │   ├── state.py                 # SimulationState
│   │   ├── enums.py                 # Enums compartidos
│   │   ├── actions.py               # Action, ActionType
│   │   ├── conditions.py            # Evaluador genérico de condiciones
│   │   ├── rng.py                   # SeededRNG
│   │   ├── content/
│   │   │   ├── __init__.py
│   │   │   ├── definitions.py       # EventDefinition, Question, Option, Outcome, …
│   │   │   ├── catalog.py           # ContentCatalog
│   │   │   └── answers.py           # Answer, RecordedAnswer, AnswerBank
│   │   ├── resolution/
│   │   │   ├── __init__.py
│   │   │   ├── conflict.py          # ConflictResolver
│   │   │   ├── effects.py           # EffectApplicator
│   │   │   └── outcomes.py          # OutcomeResolver
│   │   └── selection/
│   │       ├── __init__.py
│   │       └── event_selector.py    # EventSelector
│   └── tests/
│       ├── conftest.py              # Fixtures compartidas (opcional)
│       ├── test_state.py
│       ├── test_conditions.py
│       ├── test_answer_bank.py
│       ├── test_event_selector.py
│       ├── test_conflict_resolver.py
│       ├── test_snapshot.py
│       └── test_engine.py
└── backend/                         # Importa couple_simulator_engine (futuro)
```

---

## 3. `pyproject.toml` (metadatos mínimos)

| Campo | Valor |
|-------|-------|
| `name` | `couple-simulator-engine` |
| `requires-python` | `>=3.12` |
| `dependencies` | Ninguna en V1 (stdlib + dataclasses) |
| `optional-dependencies.dev` | `pytest`, `ruff` |
| `packages` | `couple_simulator_engine*` |

Instalación en desarrollo:

```bash
pip install -e "./couple_simulator_engine[dev]"
```

---

## 4. Módulos y responsabilidades

### 4.1 Raíz del paquete

| Archivo | Contenido | Depende de |
|---------|-----------|------------|
| `enums.py` | `LifeStage`, `RelationshipStatus`, `GameMode`, `GamePhase`, `PlayerRole`, `RunStatus`, `ActionType`, `ConditionTarget`, `EffectTarget`, `Operator`, `ConflictStrategy` | — |
| `state.py` | `SimulationState` + `clamp_stats()` | `enums` |
| `config.py` | `GameConfig` (`max_events`, pesos de conflicto, boost de AnswerBank, etc.) | `enums` |
| `rng.py` | `SeededRNG` — `random()`, `choice()`, `weighted_choice()` | stdlib |
| `actions.py` | `Action` (tipo + payload) | `enums` |
| `conditions.py` | `evaluate_condition()`, `evaluate_all()` | `definitions`, `state` |
| `session.py` | `Match`, `SimulationRun`, `LoadedGame`, `TimelineEntry`, `EventPresentation`, `EventResolution`, `EndCheck`, `GameSummary` | `state`, `config`, `rng`, `enums` |
| `snapshot.py` | `GameSnapshot` — DTO serializable para cargar/guardar estado entre requests | `session`, `content` |
| `engine.py` | `GameEngine` — orquestador principal | todos los submódulos |

### 4.2 `content/`

| Archivo | Contenido |
|---------|-----------|
| `definitions.py` | Dataclasses inmutables: `EventDefinition`, `QuestionDefinition`, `OptionDefinition`, `OutcomeDefinition`, `Condition`, `EffectDefinition`, `Distribution`, `ActionTemplate` |
| `catalog.py` | `ContentCatalog` — registro en memoria de eventos (`register`, `get`, `all_events`) |
| `answers.py` | `Answer`, `RecordedAnswer`, `AnswerBank` con `resolve_for_event()` y `has_coverage_for()` |

### 4.3 `resolution/`

| Archivo | Contenido |
|---------|-----------|
| `conflict.py` | `ConflictResolver` — encapsula estrategias (V1: `WEIGHTED_PLAYER` 65/35) |
| `effects.py` | `EffectApplicator` — aplica efectos a `SimulationState` y `event_variables` |
| `outcomes.py` | `OutcomeResolver` — elige el primer outcome cuyas condiciones se cumplen |

### 4.4 `selection/`

| Archivo | Contenido |
|---------|-----------|
| `event_selector.py` | `EventSelector` — filtra por elegibilidad, `max_occurrences`, boost si A tiene respuesta |

---

## 5. API pública (`__init__.py`)

Lo que exportan los consumidores (backend, CLI, tests):

```python
# Tipos principales
GameEngine
GameConfig
SimulationState
SimulationRun
Match
LoadedGame
GameSnapshot

# Contenido
ContentCatalog
EventDefinition
QuestionDefinition
OptionDefinition
OutcomeDefinition
Answer
AnswerBank
RecordedAnswer

# Enums de uso frecuente
GameMode
PlayerRole
Action
```

El resto de módulos son **internos**; no hace falta reexportarlos salvo necesidad explícita.

---

## 6. `GameEngine` — contrato de métodos

El engine **no mantiene estado entre requests**. Cada llamada HTTP (u otro entry point) debe **cargar el juego**, operar sobre él y **exportar el resultado** para que el adaptador lo persista.

| Método | Entrada | Salida | Notas |
|--------|---------|--------|-------|
| `load_game(snapshot)` | `GameSnapshot` | `LoadedGame` | **Obligatorio al inicio de cada request** que toque lógica de juego |
| `export_snapshot(loaded)` | `LoadedGame` | `GameSnapshot` | Tras mutar el juego; el backend persiste el snapshot |
| `create_match(mode)` | `GameMode` | `Match` | Solo partida nueva; luego `export_snapshot` |
| `start_run(loaded, player_role, seed?, config?)` | `LoadedGame`, rol | `SimulationRun` | Crea run; actualiza `loaded` internamente |
| `select_next_event(loaded)` | `LoadedGame` | `EventDefinition \| None` | Usa `loaded.run` y `loaded.answer_bank` |
| `present_event(event)` | `EventDefinition` | `EventPresentation` | Solo claves i18n; sin estado |
| `submit_answers(loaded, event, answers)` | `LoadedGame`, evento, respuestas | `EventResolution` | Pipeline completo; muta `loaded.run` |
| `check_end_conditions(loaded)` | `LoadedGame` | `EndCheck` | `max_events`, sin eventos, estado terminal |
| `build_summary(loaded)` | `LoadedGame` | `GameSummary` | Resumen final |

### 6.1 `GameSnapshot` y `LoadedGame`

`GameSnapshot` es el **contrato entre persistencia y engine**: un DTO plano (dict/dataclass) que el backend construye desde la DB. No contiene lógica.

`LoadedGame` es la **vista en memoria** que el engine usa para operar en un request:

```python
@dataclass
class GameSnapshot:
    match_id: str
    mode: GameMode
    active_run: RunSnapshot          # run en curso
    partner_a_runs: list[RunSnapshot]  # runs de A para construir AnswerBank
    config: GameConfig

@dataclass
class RunSnapshot:
    run_id: str
    player_role: PlayerRole
    run_number: int
    phase: GamePhase
    state: SimulationState           # o dict serializable
    rng_seed: int
    events_played: int
    events_played_ids: list[str]
    timeline: list[TimelineEntry]
    answers: list[RecordedAnswer]
    event_variables: dict
    status: RunStatus
    end_reason: str | None

@dataclass
class LoadedGame:
    match: Match
    run: SimulationRun               # run activa del request
    answer_bank: AnswerBank          # materializado desde runs de A
    config: GameConfig
```

`load_game()` valida el snapshot, reconstruye `SeededRNG` desde `rng_seed`, materializa `AnswerBank` desde `partner_a_runs`, y devuelve `LoadedGame` listo para `select_next_event` o `submit_answers`.

`export_snapshot()` hace el camino inverso tras mutar `loaded.run` (y, si aplica, la lista de runs de A).

### 6.2 Ciclo por request (backend)

```text
Request entrante (p. ej. POST …/answers)
  │
  ├─ 1. Backend lee DB → construye GameSnapshot
  ├─ 2. loaded = engine.load_game(snapshot)
  ├─ 3. engine.submit_answers(loaded, event, answers)   # o select_next_event, etc.
  ├─ 4. snapshot_out = engine.export_snapshot(loaded)
  └─ 5. Backend persiste snapshot_out → responde HTTP
```

Sin paso 2 no hay juego válido en memoria. Sin paso 4–5 se pierden los cambios entre requests.

---

## 7. Flujo interno de `submit_answers` (orden de llamadas)

```text
submit_answers()
  │
  ├─ 1. AnswerBank.resolve_for_event()     → respuestas de A (o None)
  ├─ 2. Aplicar option_effects de B          → EffectApplicator (STATE / EVENT_VAR)
  ├─ 3. Si hay respuesta de A:
  │       ConflictResolver por pregunta      → respuestas efectivas
  │     Si no hay respuesta de A:
  │       usar solo respuestas de B
  ├─ 4. OutcomeResolver                      → outcome ganador
  ├─ 5. Aplicar effects del outcome          → EffectApplicator
  ├─ 6. Materializar Action list             → MODIFY_STAT, SHOW_NARRATIVE, …
  ├─ 7. Actualizar run (events_played, timeline, answers)
  └─ 8. check_end_conditions()               → game_finished
```

---

## 8. Tests previstos

| Archivo | Qué valida |
|---------|------------|
| `test_state.py` | Valores iniciales, `clamp_stats()` |
| `test_conditions.py` | Operadores, targets `STATE` y `EVENT_VAR` |
| `test_answer_bank.py` | Fallback: exacto → `decision_key` → aleatorio → `None` |
| `test_event_selector.py` | Elegibilidad, `max_occurrences`, boost con AnswerBank |
| `test_conflict_resolver.py` | Match, mismatch 65/35 reproducible con semilla |
| `test_snapshot.py` | `load_game` ↔ `export_snapshot` sin pérdida de estado |
| `test_engine.py` | Smoke: cargar → operar → exportar |

Sin base de datos. Fixtures con un `EventDefinition` mínimo en memoria.

---

## 9. Integración con el backend (futuro)

```text
backend/app/services/simulation_service.py   # adaptador HTTP ↔ engine
backend/pyproject.toml                       # dependencia editable al paquete
```

El backend:

1. Carga `EventDefinition` desde su origen (JSON, DB, etc.).
2. En **cada request**: lee DB → `GameSnapshot` → `engine.load_game()`.
3. Llama al método del engine (`select_next_event`, `submit_answers`, …).
4. `engine.export_snapshot()` → persiste en DB → responde HTTP.

El engine **no sabe** que existe HTTP ni PostgreSQL. Tampoco guarda estado entre requests: **siempre** hay que llamar a `load_game()` antes de tomar una decisión.

---

## 10. Orden de implementación sugerido

1. `enums`, `state`, `config`, `rng`
2. `content/definitions`, `content/catalog`, `content/answers`
3. `conditions`, `actions`, `session`, `snapshot` (`GameSnapshot`, `LoadedGame`)
4. `resolution/effects`, `resolution/outcomes`, `resolution/conflict`
5. `selection/event_selector`
6. `engine` — incluir `load_game()` y `export_snapshot()` antes del resto de métodos
7. Tests por módulo (round-trip snapshot)
8. Adaptador en backend (fuera de este paquete)

---

## 11. Lo que **no** va en este paquete

| Responsabilidad | Dónde |
|-----------------|-------|
| Persistencia (SQLAlchemy, Alembic) | `backend/` |
| HTTP / REST | `backend/app/routers/` |
| i18n / traducción de claves | `backend/` + `frontend/` |
| UI / renderizado de acciones | `frontend/` |
| Carga de contenido desde DB | Adaptador en `backend/` |
| CLI interactiva (futuro) | Script separado que importa el engine |

---

## 12. Referencias

- [game-engine-design.md](./game-engine-design.md) — diseño funcional, modos de juego, preguntas cerradas
- [AGENTS.md](../../AGENTS.md) — convenciones del repositorio
