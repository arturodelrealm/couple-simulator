# Diseño del Game Engine

**Estado:** Borrador — en refinamiento  
**Ámbito:** Paquete Python independiente (`couple_simulator_engine/`) importado por el backend y otros entry points  
**Relacionado:** [overview.md](../overview.md), [AGENTS.md](../../AGENTS.md), [backlog §5–7](../backlog/backlog_simulador_vida_pareja.md), [.cursor/rules/game-engine.mdc](../../.cursor/rules/game-engine.mdc)

---

## 1. Resumen

El **game engine** es el núcleo de simulación del Couple Life Simulator. Recibe un estado inicial, presenta eventos con preguntas, recibe respuestas de uno o dos jugadores, y devuelve **acciones** estructuradas que describen qué cambió en la simulación y qué debe mostrar la interfaz.

El motor es **agnóstico del canal de entrada**: el backend FastAPI, una CLI de consola, tests unitarios o futuros clientes consumen la misma API de clases. El backend se encarga de persistencia, HTTP e i18n; el engine solo de lógica de juego.

### Principios de diseño

| Principio | Implicación |
|-----------|-------------|
| **Contenido separado del código** | Eventos, preguntas, opciones, condiciones y efectos son **datos** evaluados por reglas genéricas. Sin `if evento == "casino"` en el engine. |
| **Respuesta ≠ resultado** | Las respuestas de cada jugador se conservan siempre, aunque las reglas de resolución cambien después. |
| **Caja negra** | Quien llama al engine envía respuestas y recibe acciones; el *cómo* se resuelven los conflictos o la aleatoriedad es responsabilidad interna del engine. |
| **Acciones como salida** | El resultado de resolver un evento es una **lista de acciones** (cambiar stat, mostrar narrativa, entrada en timeline, terminar juego, etc.), no solo un delta de estado. |
| **No sobre-diseñar V1** | Efectos explícitos por opción y compatibilidad match/mismatch son suficientes para el primer juego jugable; el diseño deja espacio para crecer. |
| **Realismo = contenido, no engine** | El motor evalúa reglas genéricas; el realismo viene de tener **muchos eventos** (~100) con condiciones contextuales. No se resuelve repitiendo la misma pregunta con distintos umbrales de dinero. |
| **Pocas variables de estado** | El catálogo de stats es **fijo y acotado** (ver §5.1). La riqueza del juego está en los eventos, no en multiplicar variables. |

---

## 2. Objetivo del juego

Simular la vida de una pareja (o de una persona en modo solo) a través de **eventos** con **preguntas** y **opciones**. Cada decisión modifica un **estado de simulación** representado por variables numéricas y de contexto. El juego termina cuando se cumple una condición de fin y entrega un **resumen** con estadísticas finales y una línea de tiempo.

### Flujo de alto nivel

```text
Estado inicial
      │
      ▼
┌─────────────────────────────────────┐
│  Engine elige evento elegible       │  ← condiciones + aleatoriedad
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  Presentación del evento            │  ← narrativa previa (solo UX)
│  + preguntas con opciones           │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  Jugador(es) responden              │  ← 1 respuesta (solo) o 2 (pareja)
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  Engine resuelve consecuencias      │  ← efectos, outcomes, RNG, conflictos
│  → lista de Action                  │
└─────────────────────────────────────┘
      │
      ▼
Actualizar estado + timeline
      │
      ├── ¿Fin de juego? ──→ Resumen final
      │
      └── Repetir
```

### 2.1 Realismo y escala de contenido

El realismo **no depende del engine**, sino de la **cantidad y variedad de eventos**. Para que «comprar una casa» solo aparezca cuando la pareja tiene nivel económico suficiente, hace falta un evento con condiciones de elegibilidad (`finances >= 40`), no una pregunta genérica repetida con distintos umbrales.

| Enfoque | Problema |
|---------|----------|
| Pocas preguntas genéricas con parámetros variables | Partner A respondería «¿comprarías casa con $?», luego «con $$?», luego «con $$$ y un hijo?» — tedioso e irreal |
| **Muchos eventos específicos** con condiciones de contexto | Cada evento ocurre solo cuando el estado lo permite; la experiencia es variada sin sobrecargar al jugador |

**Objetivo de catálogo:** ~100 eventos en producción, cada uno con condiciones de elegibilidad, preguntas y outcomes propios. El engine solo filtra y elige; quien crea contenido aporta el realismo.

**Variables de estado:** se mantiene un conjunto **pequeño y estable** (§5.1). No se añaden stats por evento. Las señales intermedias de un evento usan `event_variables` temporales, que se descartan al resolver.

---

## 3. Ubicación en el repositorio

```text
couple-simulator/
├── couple_simulator_engine/  # Paquete Python independiente (sin FastAPI, sin SQLAlchemy)
│   ├── pyproject.toml
│   ├── couple_simulator_engine/
│   │   ├── __init__.py
│   │   ├── engine.py         # GameEngine — orquestador principal
│   │   ├── session.py        # GameSession, fase de juego
│   │   ├── state.py          # SimulationState, LifeStage
│   │   ├── content/          # Definiciones data-driven (Event, Question, …)
│   │   ├── resolution/       # OutcomeResolver, EffectApplicator, ConflictResolver
│   │   ├── selection/        # EventSelector
│   │   ├── actions.py        # Tipos de Action (salida del engine)
│   │   ├── conditions.py     # Evaluador genérico de condiciones
│   │   └── rng.py            # RNG con semilla (reproducible en tests)
│   └── tests/
├── backend/                  # Importa couple_simulator_engine como dependencia local
│   └── app/services/         # Adaptadores: DB ↔ engine, HTTP ↔ engine
└── ...
```

El backend declara el engine como dependencia editable:

```toml
# backend/pyproject.toml (futuro)
dependencies = [
    "couple-simulator-engine @ file:///${PROJECT_ROOT}/couple_simulator_engine",
]
```

O vía monorepo con `pip install -e "../couple_simulator_engine"` en desarrollo.

**Regla:** el paquete `couple_simulator_engine` no importa nada de `backend/app`. La dependencia va en una sola dirección.

---

## 4. Entry points

El engine expone una API de objetos Python. Cada entry point es un **adaptador fino**:

| Entry point | Responsabilidad del adaptador |
|-------------|-------------------------------|
| **Backend (FastAPI)** | Cargar/guardar sesión en DB, mapear schemas HTTP ↔ tipos del engine, traducir claves i18n en mensajes de error |
| **Consola (CLI)** | Leer input del terminal, imprimir narrativa y stats, cargar contenido desde JSON/YAML local |
| **Tests** | Semilla fija de RNG, contenido mínimo en memoria, aserciones sobre acciones y estado |

```text
                    ┌─────────────────────────┐
                    │  couple_simulator_engine │
                    │  (puro)                  │
                    └───────────┬─────────────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    Backend service    CLI runner      pytest
```

---

## 5. Modelo de dominio (clases)

### 5.1 Estado de simulación

Conjunto **canónico y cerrado** para V1. No se añaden variables de estado por evento; la complejidad vive en el catálogo de eventos.

| Variable | Tipo | Rango / valores | Rol |
|----------|------|-----------------|-----|
| `age` | `int` | ≥ 18, sin máximo fijo en V1 | Tiempo narrativo; dispara etapas de vida |
| `compatibility` | `int` | 0–100 | Salud de la relación; eje central del modo pareja |
| `finances` | `int` | 0–100 | Nivel económico abstracto (no simulación monetaria real) |
| `adventures` | `int` | 0–100 | Apertura a experiencias / riesgo |
| `career` | `int` | 0–100 | Progreso profesional |
| `quality_of_life` | `int` | 0–100 | Bienestar general |
| `children` | `int` | ≥ 0 | Cantidad de hijos |
| `relationship_status` | `enum` | `together` \| `separated` \| `widowed` | Fin de juego / elegibilidad de eventos |
| `life_stage` | `enum` | `youth` \| `adult` \| `elderly` | Filtro de eventos por etapa |

```python
@dataclass
class SimulationState:
    age: int = 22
    compatibility: int = 100
    finances: int = 50
    adventures: int = 50
    career: int = 50
    quality_of_life: int = 50
    children: int = 0
    relationship_status: RelationshipStatus = RelationshipStatus.TOGETHER
    life_stage: LifeStage = LifeStage.YOUTH
```

Los stats numéricos (salvo `children` y `age`) se **clamp** a 0–100 tras cada efecto. `event_variables` (§10) son temporales y **no** forman parte del estado persistente.

### 5.2 Partida, simulación y sesión

Una **partida** (`Match`) puede tener **varias simulaciones** por jugador. Partner A puede jugar en solitario varias veces; Partner B puede rejugar. Los eventos entre runs pueden coincidir o no. Cada ejecución es un `SimulationRun` independiente con su propio estado, timeline y respuestas.

```python
@dataclass
class Match:
    match_id: UUID
    mode: GameMode
    runs: list[SimulationRun]        # historial de simulaciones A y B

@dataclass
class SimulationRun:
    run_id: UUID
    match_id: UUID
    player_role: PlayerRole          # partner_a | partner_b
    run_number: int                  # 1, 2, 3… por rol
    phase: GamePhase                 # ver §6
    state: SimulationState
    config: GameConfig
    rng: SeededRNG
    events_played: int
    events_played_ids: list[str]     # IDs de eventos ya resueltos en esta run
    timeline: list[TimelineEntry]
    answers: list[RecordedAnswer]    # respuestas de esta run
    event_variables: dict[str, Any]  # variables internas del evento en curso
    status: RunStatus                # ACTIVE | FINISHED
    end_reason: str | None

@dataclass
class RecordedAnswer:
    event_id: str
    decision_key: str              # clave de familia para fallback (ver §6.4)
    question_id: str
    option_id: str
    player: PlayerRole
    state_snapshot: SimulationState  # estado al momento de responder (para fallback contextual)
    run_id: UUID
```

El **banco de respuestas de Partner A** no es un solo dict por `event_id`: es la **unión de todas las respuestas** de sus `SimulationRun` completadas o en curso. El backend persiste runs y respuestas; el engine recibe el banco ya materializado al resolver la run de B.

```python
@dataclass
class AnswerBank:
    """Todas las respuestas de A acumuladas en sus runs de pre-juego."""
    entries: list[RecordedAnswer]

    def resolve_for_event(
        self, event: EventDefinition, current_state: SimulationState
    ) -> list[Answer] | None:
        """Fallback: exact match → decision_key → elección aleatoria entre candidatos. Ver §6.4."""
        ...
```

### 5.3 Configuración de partida

```python
@dataclass
class GameConfig:
    max_events: int = 10                    # eventos por SimulationRun; configurable al crear partida
    conflict_partner_b_weight: float = 0.65
    conflict_partner_a_weight: float = 0.35
    compatibility_mismatch_penalty: int = 5
    answer_bank_preference_boost: float = 2.0  # multiplicador de peso si A tiene respuesta (§6.2)
```

### 5.4 Contenido (data-driven)

Definiciones inmutables cargadas desde JSON/YAML o desde filas de DB serializadas a dict:

```python
@dataclass
class EventDefinition:
    id: str
    decision_key: str               # familia de decisión para fallback (§6.4), p. ej. "buy_house"
    title_key: str                  # clave i18n; el engine no traduce
    description_key: str | None
    preamble_key: str | None        # conversación previa (solo presentación)
    life_stage: LifeStage | None
    tags: list[str]                 # p. ej. ["financial", "couple_only"]
    eligibility_conditions: list[Condition]
    questions: list[QuestionDefinition]
    outcomes: list[OutcomeDefinition]
    weight: float = 1.0             # para selección aleatoria ponderada
    max_occurrences: int = 1        # por SimulationRun: 1 = único; >1 permite repetir en la misma run
    couple_only: bool = False

@dataclass
class QuestionDefinition:
    id: str
    decision_key: str | None        # opcional; hereda de event si None
    text_key: str
    order: int
    options: list[OptionDefinition]

@dataclass
class OptionDefinition:
    id: str
    text_key: str
    option_effects: list[EffectDefinition]   # efectos inmediatos / variables internas
    # En pareja: puede haber efectos distintos según quién eligió (futuro)

@dataclass
class OutcomeDefinition:
    id: str
    name_key: str
    order: int                        # primera que cumple condiciones gana
    conditions: list[Condition]
    effects: list[EffectDefinition]
    actions: list[ActionTemplate]     # narrativa, timeline, etc.

@dataclass
class Condition:
    target: ConditionTarget           # STATE | EVENT_VAR | ANSWER | MODE
    variable: str
    operator: Operator                # EQ, NEQ, GT, GTE, LT, LTE, IN
    value: Any
```

### 5.5 Respuestas

```python
@dataclass
class Answer:
    question_id: str
    option_id: str
    player: PlayerRole | None         # None en modo solo
```

Las respuestas se almacenan **siempre**, independientemente del outcome.

### 5.6 Efectos

```python
@dataclass
class EffectDefinition:
    target: EffectTarget              # STATE | EVENT_VAR
    variable: str
    value: int | float | str
    distribution: Distribution | None # None = valor fijo; ver §8

@dataclass
class Distribution:
    kind: Literal["fixed", "uniform", "normal"]
    # normal: median (μ), std (σ), opcional min/max tras muestreo
    params: dict[str, float]
```

### 5.7 Acciones (salida del engine)

El engine **no renderiza UI**. Devuelve acciones tipadas que el consumidor interpreta:

```python
class ActionType(str, Enum):
    MODIFY_STAT = "modify_stat"
    SHOW_NARRATIVE = "show_narrative"
    ADD_TIMELINE_ENTRY = "add_timeline_entry"
    UPDATE_AVATAR_HINT = "update_avatar_hint"
    END_GAME = "end_game"
    ADVANCE_LIFE_STAGE = "advance_life_stage"

@dataclass
class Action:
    type: ActionType
    payload: dict[str, Any]
```

Ejemplos de `payload`:

```python
# MODIFY_STAT
{"variable": "compatibility", "delta": -8, "new_value": 72}

# SHOW_NARRATIVE
{"text_key": "events.vacation.conflict.beach_wins", "params": {"winner": "partner_b"}}

# ADD_TIMELINE_ENTRY
{"title_key": "...", "description_key": "...", "category": "relationship", "age": 28}

# END_GAME
{"reason": "separation", "reason_key": "game.end.separation"}
```

### 5.8 Resultado de un paso

```python
@dataclass
class EventResolution:
    event_id: str
    outcome_id: str | None
    actions: list[Action]
    state: SimulationState            # estado ya actualizado
    answers_recorded: list[Answer]
    game_finished: bool
```

---

## 6. Modos de juego y fases

### 6.1 Modo solo (`SOLO`) — pre-juego de Partner A

El modo solo **no es un producto independiente en V1**: existe únicamente para que **Partner A llene el `AnswerBank`** durante la fase de pre-juego en modo pareja.

Un jugador responde todas las preguntas del evento. La resolución es directa:

1. Aplicar `option_effects` de cada respuesta (variables internas del evento y/o estado).
2. Evaluar `outcomes` en orden hasta que una condición se cumpla.
3. Aplicar efectos y acciones del outcome elegido.
4. Emitir lista final de `Action`.

El engine es la **única fuente de verdad** del estado: los `option_effects` con `target: STATE` modifican `SimulationState` **antes** de evaluar el outcome (ver §10).

### 6.2 Modo pareja (`COUPLE`) — flujo asíncrono

El modo pareja tiene **dos fases** desacopladas en el tiempo. Los eventos de A y B **pueden coincidir, pero no están forzados a ser los mismos**: cada run elige eventos según elegibilidad y aleatoriedad. En la fase B, el engine **prefiere** eventos para los que ya existe respuesta de A en el `AnswerBank` (mejor experiencia), sin exigirla.

```text
Match (partida)
  │
  ├── SimulationRun A-1, A-2, … (pre-juego, modo solo)
  │     Partner A juega la simulación completa varias veces (sin mínimo obligatorio)
  │     Cada run: eventos aleatorios elegibles → responde → estado evoluciona
  │     Respuestas + state_snapshot → AnswerBank acumulado
  │
  └── SimulationRun B-1, B-2, … (juego activo / rejugar)
        Partner B juega eventos elegibles en su propia run
        El engine PREFIERE eventos con cobertura en AnswerBank (peso extra)
        Si hay respuesta de A → comparación / conflicto; si no → solo responde B
        B responde en vivo → resolución → acciones
```

```python
class GamePhase(str, Enum):
    PARTNER_A_PREPLAY = "partner_a_preplay"   # A juega solo, acumula banco
    PARTNER_B_PLAY = "partner_b_play"         # B juega con fallback de A
    FINISHED = "finished"

class GameMode(str, Enum):
    SOLO = "solo"
    COUPLE = "couple"
```

#### Fase A — Partner A (pre-juego)

- A puede ejecutar **cero o más `SimulationRun` en modo solo** — **no hay mínimo obligatorio** antes de que B juegue.
- Cada run **sí avanza `SimulationState`**: la simulación es real dentro de esa run.
- Al resolver cada evento, las respuestas se registran en `RecordedAnswer` con `decision_key` y `state_snapshot`.
- Las runs de A son **independientes** entre sí (estado inicial en cada una), pero todas alimentan el mismo `AnswerBank` de la partida.
- Cuantas más runs complete A, más rico queda el banco y mejor la experiencia de B; no es requisito bloqueante.

#### Fase B — Partner B (juego activo)

- B inicia su propia `SimulationRun` con estado inicial estándar. La run termina al alcanzar `config.max_events` (default **10**, configurable).
- El engine elige el siguiente evento entre los elegibles en el estado de B, respetando `max_occurrences` por evento en esa run.
- **Preferencia por cobertura de A:** entre eventos elegibles, los que tienen respuesta en `AnswerBank` (match exacto o vía `decision_key`) reciben un **boost de peso** (`GameConfig.answer_bank_preference_boost`). No se filtran los demás: pueden salir igualmente.
- Para cada evento de B:
  - Si `AnswerBank` resuelve respuesta de A → comparar con B → `ConflictResolver` si hay mismatch.
  - Si **no** hay respuesta de A → resolver **solo con las respuestas de B** (mismo flujo que modo solo); no hay error ni bloqueo.

```python
def resolve_event(
    run: SimulationRun,
    event: EventDefinition,
    partner_b_answers: list[Answer],
    partner_a_bank: AnswerBank,
) -> EventResolution:
    partner_a_answers = partner_a_bank.resolve_for_event(event, run.state)
    ...
```

#### Rejugar

- Una misma partida admite **múltiples runs de B** (p. ej. volver a jugar en la despedida).
- Cada run de B es independiente; reutiliza el `AnswerBank` de A acumulado hasta ese momento.
- A también puede añadir más runs de pre-juego antes de que B juegue de nuevo.

### 6.3 Resolución de conflictos (pareja)

Solo aplica cuando **existe respuesta inferida de A** para el evento. Si el `AnswerBank` no devuelve nada, se omite el paso de conflicto y la resolución usa únicamente las respuestas de B.

Cuando la respuesta inferida de A y la respuesta en vivo de B difieren, el engine delega en `ConflictResolver` — **encapsulado**, intercambiable, sin lógica por evento.

| Estrategia | Comportamiento |
|------------|----------------|
| `WEIGHTED_PLAYER` **(default V1)** | Elige la opción de A con peso 35% o la de B con peso 65% |
| `PRIORITY_PLAYER` | Gana siempre un rol fijo |
| `COMPROMISE` | Outcome de conflicto predefinido en datos |
| `STAT_WEIGHTED` | Favorece al jugador con mayor stat X |

**V1:** `WEIGHTED_PLAYER` con proporción **65% partner_b / 35% partner_a**. Las **consecuencias** del mismatch (stats, narrativa) se definen en el contenido del evento (`mismatch_actions`, outcomes con `flag: has_mismatch`) — ver [game-event-content-model.md §8.5](./game-event-content-model.md). El engine solo decide qué opción gana el conflicto.

El resultado del conflicto alimenta las reglas de outcomes: condiciones sobre `answers_match`, `winning_player`, etc.

### 6.4 Banco de respuestas y fallback (estilo i18n)

Partner A no puede responder cada variante contextual de un evento («casa con $», «casa con $$ y un hijo», etc.). En su lugar, las respuestas se organizan por **`decision_key`** — análogo a una clave de traducción.

```text
decision_key: "buy_house"
  ├── event_id exacto: "buy_house_finances_60_child_1"  → respuesta SÍ (run A-2)
  ├── event_id exacto: "buy_house_finances_40"         → respuesta NO  (run A-1)
  └── fallback por decision_key: "buy_house"            → última respuesta registrada
```

**Algoritmo de resolución** (`AnswerBank.resolve_for_event`):

1. **Match exacto** por `event_id` + `question_id` en cualquier run de A.
2. **Match por `decision_key`** + pregunta equivalente (misma `decision_key` en `QuestionDefinition`).
3. **Entre candidatos con la misma `decision_key`:** elegir uno **al azar** (RNG del engine).
4. **Fallback genérico:** última respuesta registrada para esa `decision_key`.
5. Si no hay entrada: devolver `None` → la resolución del evento continúa **solo con B** (§6.3).

**Ejemplo:**

- A respondió **SÍ** a `buy_house_finances_40` (`decision_key: buy_house`, `finances: 42`).
- B enfrenta `buy_house_finances_60_child_1` (`finances: 65`, `children: 1`).
- No hay match exacto → fallback por `decision_key` (elección aleatoria entre candidatos) → se asume **SÍ**.
- No es ideal, pero evita tedio y se acerca a «lo que A habría elegido» sin preguntarle cada variante.

Las opciones de una pregunta deben ser **comparables entre variantes** del mismo `decision_key` (mismos `option_id` semánticos: `yes`, `no`, `maybe`, etc.).

---

## 7. Bucle del juego (`GameEngine`)

Clase orquestadora principal. El engine es **stateless entre requests**: no guarda partidas en memoria. Cada operación empieza con `load_game()` y termina con `export_snapshot()` para que el adaptador (backend) persista.

```python
class GameEngine:
    def __init__(self, content: ContentCatalog, config: GameConfig): ...

    def load_game(self, snapshot: GameSnapshot) -> LoadedGame:
        """Reconstruye Match, SimulationRun activa y AnswerBank desde persistencia."""

    def export_snapshot(self, loaded: LoadedGame) -> GameSnapshot:
        """Serializa el estado tras mutar el juego; el backend lo guarda en DB."""

    def start_run(
        self,
        loaded: LoadedGame,
        player_role: PlayerRole,
        *,
        seed: int | None = None,
    ) -> SimulationRun: ...

    def select_next_event(self, loaded: LoadedGame) -> EventDefinition | None:
        """Usa loaded.run y loaded.answer_bank. Boost en fase B si A tiene respuesta."""

    def present_event(self, event: EventDefinition) -> EventPresentation:
        """Datos para UI: preamble, preguntas, opciones (solo claves i18n)."""

    def submit_answers(
        self,
        loaded: LoadedGame,
        event: EventDefinition,
        answers: list[Answer],
    ) -> EventResolution: ...

    def check_end_conditions(self, loaded: LoadedGame) -> EndCheck: ...

    def build_summary(self, loaded: LoadedGame) -> GameSummary: ...
```

### Hidratación: `GameSnapshot` → `LoadedGame`

El backend construye un `GameSnapshot` desde la DB en **cada request** que toque el juego (pedir evento, enviar respuesta, consultar resumen). El snapshot incluye la run activa y las runs de Partner A necesarias para el `AnswerBank`.

`load_game()` es obligatorio antes de `select_next_event` o `submit_answers`. Sin él no hay estado válido en memoria.

Tras mutar el juego, `export_snapshot()` devuelve el DTO actualizado para persistir. Ver [package skeleton §6](./couple-simulator-engine-package-skeleton.md) para la estructura de `GameSnapshot` y `RunSnapshot`.

### Condiciones de fin de juego

| Condición | Ejemplo |
|-----------|---------|
| Cuota de eventos alcanzada | `events_played >= config.max_events` |
| Sin eventos elegibles restantes | Pool agotado |
| Acción `END_GAME` | Separación, muerte |
| Estado terminal | `relationship_status == "separated"` |

### Resumen final (`GameSummary`)

```python
@dataclass
class GameSummary:
    final_state: SimulationState
    compatibility: int
    timeline: list[TimelineEntry]
    highlights: list[str]           # claves i18n o texto generado por plantilla
    events_played: int
    end_reason: str | None
```

---

## 8. Aleatoriedad

El engine centraliza RNG con **semilla opcional** para reproducibilidad en tests y debugging.

| Caso de uso | Mecanismo |
|-------------|-----------|
| Selección de evento | Peso (`weight`) entre eventos elegibles |
| Preferencia fase B | Boost si `AnswerBank` tiene cobertura para el evento |
| Outcome con varias opciones válidas | Primera por orden, o ponderada si se configura |
| Efecto con `distribution: normal` | Muestreo N(μ, σ), luego clamp al rango del stat |
| Apuesta de casino (sí → resultado aleatorio) | Outcome con condición sobre respuesta + ramas con probabilidad |
| Conflicto pareja `RANDOM` | Elección pseudoaleatoria entre opciones |

```python
# Ejemplo: efecto con distribución normal
{
  "target": "STATE",
  "variable": "compatibility",
  "distribution": {"kind": "normal", "params": {"median": 10, "std": 3}},
}
# El valor aplicado puede ser 7, 10, 13…; el engine registra el delta real en la Action.
```

---

## 9. Condiciones de elegibilidad de eventos

Un evento solo entra al pool si **todas** sus `eligibility_conditions` se cumplen contra el estado actual (y opcionalmente contexto de sesión):

```json
{
  "id": "buy_house",
  "eligibility_conditions": [
    {"target": "STATE", "variable": "finances", "operator": "GTE", "value": 40},
    {"target": "STATE", "variable": "age", "operator": "GTE", "value": 25}
  ]
}
```

Operadores: `EQ`, `NEQ`, `GT`, `GTE`, `LT`, `LTE`, `IN`.

Esto garantiza realismo contextual sin lógica por evento en código.

---

## 10. Resolución de un evento (detalle)

```text
Evento E con preguntas Q1…Qn
        │
        ├─ Por cada respuesta (orden del engine):
        │     aplicar option_effects → event_variables y/o SimulationState
        │     (target: STATE modifica el estado antes del outcome; el engine es la fuente de verdad)
        │
        ├─ (Pareja, solo si hay respuesta de A) Resolver conflictos pregunta a pregunta
        │     → respuestas «efectivas» para evaluación
        │     (sin respuesta de A → solo respuestas de B)
        │
        ├─ Evaluar outcomes en orden (order asc):
        │     primera cuyas conditions se cumplen → outcome ganador
        │
        ├─ Aplicar effects del outcome
        │
        └─ Materializar Action list:
              MODIFY_STAT, SHOW_NARRATIVE, ADD_TIMELINE_ENTRY, …
```

### Variables internas del evento

Acumulan señales de las respuestas antes del outcome final (ejemplo del backlog — comprar casa):

```text
Pregunta 1 → home_desire +3 / +1 / -2
Pregunta 2 → home_budget +1 / +2 / +3

Outcome «compran casa» si home_desire >= 4 AND home_budget >= 2
```

Las variables internas viven en `session.event_variables` durante el evento y se descartan al resolver.

---

## 11. Etapas de vida

```python
class LifeStage(str, Enum):
    YOUTH = "youth"       # ~20–40
    ADULT = "adult"       # 40–60
    ELDERLY = "elderly"   # 60+
```

Transición por **edad** tras aplicar efectos (`age` en estado) o por acción explícita `ADVANCE_LIFE_STAGE`. Los eventos pueden filtrarse por `life_stage` en elegibilidad.

No se simula año a año: un evento puede representar un salto temporal narrativo.

---

## 12. Relación engine ↔ backend

| Responsabilidad | Engine | Backend |
|-----------------|--------|---------|
| Reglas de juego | ✅ | ❌ |
| Persistencia (SQLAlchemy) | ❌ | ✅ |
| HTTP / autenticación | ❌ | ✅ |
| Cargar `EventDefinition` desde DB/JSON | ❌ (recibe objetos) | ✅ adaptador |
| Leer DB → `GameSnapshot` | ❌ | ✅ en cada request |
| `load_game()` / `export_snapshot()` | ✅ | ❌ |
| Persistir snapshot tras cada paso | ❌ | ✅ |
| Materializar `AnswerBank` desde runs de A | ✅ (en `load_game`) | ✅ (provee datos en snapshot) |
| Traducción i18n al usuario | ❌ (solo claves) | ✅ / frontend |
| Semilla RNG por run | ✅ | guarda `rng_seed` en snapshot |

Flujo típico en backend (cada request):

```text
POST /games/{id}/runs  (player_role=partner_a)     ← partida nueva
  → engine.start_run(loaded, …)
  → export_snapshot → persistir

POST /games/{id}/runs/{run_id}/events/next
  → DB → GameSnapshot → load_game()
  → select_next_event(loaded)
  → export_snapshot → persistir → EventPresentation

POST /games/{id}/runs/{run_id}/events/{event_id}/answers
  → DB → GameSnapshot → load_game()
  → submit_answers(loaded, event, answers)
  → export_snapshot → persistir → actions + state

POST /games/{id}/runs  (player_role=partner_b)     ← nueva run de B
  → load_game() → start_run() → export_snapshot → persistir
```

---

## 13. Ejemplo completo (modo pareja)

**Contexto:** A jugó 2 runs de pre-juego. En una respondió SÍ a `buy_house_finances_40`. B inicia su run y enfrenta un evento distinto.

**Evento de B:** Vacaciones (`vacation_destination_mountain`, `decision_key: vacation_destination`)

| Pregunta | Opciones |
|----------|----------|
| ¿A dónde vamos? | `beach` / `mountain` / `city` |

**Partner A** (fallback desde banco): respondió `beach` en `vacation_destination_beach` (run A-1)  
**Partner B** (en vivo): `mountain`

1. Engine resuelve respuesta de A vía `decision_key` (no hay match exacto de evento).
2. Detecta mismatch entre `beach` y `mountain`.
3. `ConflictResolver` (`WEIGHTED_PLAYER` 65/35) → con 65% de probabilidad gana B → opción efectiva `mountain`.
4. Outcome `conflict_mountain_wins`: `compatibility` -5, `SHOW_NARRATIVE`, `ADD_TIMELINE_ENTRY`.
5. Actions devueltas al frontend para renderizar.

---

## 14. Alcance V1 vs futuro

### V1 (primer juego jugable)

- [ ] Paquete `couple_simulator_engine` importable, tests unitarios sin DB
- [ ] `SimulationState` con el catálogo cerrado de §5.1
- [ ] `GameConfig.max_events` configurable (default 10)
- [ ] `load_game()` / `export_snapshot()` con round-trip de `GameSnapshot`
- [ ] `SimulationRun` + `AnswerBank` con fallback por `decision_key`
- [ ] Modo `COUPLE`: fase A (solo para llenar banco, sin mínimo) + fase B (preferencia por eventos con respuesta de A)
- [ ] `ConflictResolver` encapsulado con `WEIGHTED_PLAYER` 65/35
- [ ] `option_effects` con `target: STATE` aplicados antes del outcome
- [ ] Acciones: `MODIFY_STAT`, `ADD_TIMELINE_ENTRY`, `SHOW_NARRATIVE`, `END_GAME`
- [ ] `max_occurrences` por evento (1 o más)
- [ ] ~15–20 eventos de prueba (camino a ~100 en producción)

### Post-V1

- Modo solo como producto independiente (fuera del flujo pareja)
- Opción fase A «solo recolección» sin avanzar estado
- Distribuciones normales/uniformes en efectos
- Estrategias de conflicto configurables por evento
- Rejugar B con UI dedicada
- Evolución de avatar por etapa
- Hijos como entidad con nombre/avatar
- Resumen narrativo generado por plantillas más ricas
- Catálogo completo ~100 eventos

---

## 15. Preguntas abiertas

_No hay preguntas pendientes por ahora._ Nuevas dudas se añaden aquí conforme surjan.

### Respondidas

#### P1 — ¿Cuántos eventos responde Partner A? *(2026-08-29)*

**Decisión:** A **juega la simulación en modo solo varias veces** (varias `SimulationRun`). Cada run recorre eventos aleatorios elegibles y acumula respuestas en el `AnswerBank`. No responde un cuestionario fijo de 100 preguntas.

El fallback por `decision_key` (§6.4) cubre variantes contextuales que A no jugó exactamente.

---

#### P2 — ¿Partner B ve los mismos eventos que A? *(2026-08-29, actualizado)*

**Decisión:** **No están forzados a ser los mismos**, pero **pueden coincidir**. B juega eventos elegibles en su propia run; el engine **prefiere** (mayor peso) los que ya tienen respuesta en el `AnswerBank` de A.

Una misma partida admite **múltiples simulaciones** por jugador (A puede jugar N veces; B puede rejugar M veces), cada una como `SimulationRun` independiente.

---

#### P3 — ¿Se simula estado durante la fase A? *(2026-08-29)*

**Decisión:** **Sí** — cada run de A avanza `SimulationState` de verdad. Hace el pre-juego más dinámico y menos tedioso.

**V1:** implementar simulación completa en fase A. **Futuro:** valorar también el modo «solo recolección» sin estado (más simple).

---

#### P4 — ¿Dónde vive el contenido? *(2026-08-29)*

**Decisión:** **Fuera del alcance del engine.** El motor recibe `EventDefinition` ya materializados; quien lo consume (backend, CLI) decide si cargan desde JSON, DB u otro origen.

---

#### P5 — Algoritmo default de conflicto en pareja *(2026-08-29)*

**Decisión:** `ConflictResolver` encapsulado. **V1:** estrategia `WEIGHTED_PLAYER` 65/35. Penalizaciones y narrativa de mismatch vía contenido declarativo, no regla fija en `GameConfig`.

---

#### P6 — ¿Los eventos pueden repetirse? *(2026-08-29)*

**Decisión:** Cada evento define su propio `max_occurrences` por `SimulationRun`: **1 o más**. Un valor de 1 impide repetir el mismo evento dentro de la misma run; valores mayores lo permiten.

---

#### P7 — ¿Cómo se fija `max_events` por run? *(2026-08-29)*

**Decisión:** **Configurable** al crear la partida vía `GameConfig.max_events`. **Default: 10** eventos por `SimulationRun`.

---

#### P8 — ¿Modo `SOLO` en V1? *(2026-08-29)*

**Decisión:** El modo solo **solo existe para que A llene el `AnswerBank`** en el flujo pareja. No hay modo solo como producto independiente en V1.

---

#### P9 — Nombre del paquete Python *(2026-08-29)*

**Decisión:** `couple_simulator_engine` — `from couple_simulator_engine import GameEngine`.

---

#### P10 — ¿`option_effects` modifican `SimulationState` antes del outcome? *(2026-08-29)*

**Decisión:** **Sí.** Si `target: STATE`, el engine aplica el cambio **antes** de evaluar outcomes. Si `target: EVENT_VAR`, solo acumula variables internas del evento. **El engine es la única fuente de verdad** del estado de simulación.

---

#### P11 — ¿Mínimo de runs de pre-juego para A? *(2026-08-29)*

**Decisión:** **No hay mínimo.** B puede jugar aunque A no haya hecho ninguna run. Si no existe respuesta de A para un evento de B, la resolución usa **solo las respuestas de B** (sin conflicto). La experiencia mejora cuando A ya respondió, pero **nunca es obligatorio**.

---

#### P12 — Fallback contextual en `AnswerBank` *(2026-08-29)*

**Decisión:** Entre candidatos con la misma `decision_key`, la elección es **aleatoria** (RNG del engine), no por distancia de estado.

---

## 16. Próximos pasos

1. Definir esquema de `decision_key` y convención de `option_id` para el catálogo de eventos.
2. Implementar el paquete siguiendo [couple-simulator-engine-package-skeleton.md](./couple-simulator-engine-package-skeleton.md).
3. Tests unitarios: fallback aleatorio, preferencia de eventos con cobertura de A, conflicto 65/35, resolución sin respuesta de A.
4. Adaptador mínimo en backend + CLI de consola para validar el loop sin frontend.

---

## 17. Referencias

- [overview.md](../overview.md) — reglas de producto (data-driven, acciones, timeline)
- [couple-simulator-engine-package-skeleton.md](./couple-simulator-engine-package-skeleton.md) — esqueleto del paquete Python
- [game-event-content-model.md](./game-event-content-model.md) — eventos, preguntas, `one_of`, mismatch declarativo, interpolación
- [backlog §5–7](../backlog/backlog_simulador_vida_pareja.md) — modelos de dominio y flujo de resolución
- [AGENTS.md](../../AGENTS.md) — stats iniciales, etapas de vida, estados de partida
- [game-lobby spec](./game-lobby-and-player-a-setup.md) — `game_mode`, roles, fases de partida
