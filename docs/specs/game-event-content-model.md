# Modelo de contenido: eventos, preguntas y acciones

**Estado:** Borrador — en refinamiento  
**Ámbito:** Forma de los datos de contenido que consume el engine (no implementación)  
**Relacionado:** [game-engine-design.md](./game-engine-design.md), [couple-simulator-engine-package-skeleton.md](./couple-simulator-engine-package-skeleton.md)

---

## 1. Resumen

Un **evento** es la unidad de contenido del juego. Agrupa:

- **Condiciones de elegibilidad** (¿cuándo puede ocurrir?)
- **Presentación** (narrativa previa, título — solo UX)
- **Preguntas** con **opciones**
- **Plantillas de acciones** que el engine **materializa** tras procesar respuestas, efectos y aleatoriedad

El contenido describe *intención*; el engine devuelve *acciones resueltas* (`Action` con valores concretos). Nunca se retornan plantillas crudas al frontend.

---

## 2. Principios

| Principio | Implicación |
|-----------|-------------|
| **Data-driven** | Sin `if evento == "casino"` en código. Todo en definiciones. |
| **Tags, no tipos rígidos (V1)** | Clasificación vía `tags` conocidos por el backend; no hace falta un enum `event_type` al inicio. |
| **Condiciones como árbol** | Soporte explícito de AND / OR / NOT con un evaluador genérico. |
| **Dos capas de consecuencias** | Efectos por **opción** (inmediatos, acumulan señales) + **outcomes** por evento (evaluados al final). |
| **Plantilla ≠ acción** | El contenido define `ActionTemplate`; el engine produce `Action` tras RNG y reglas. |
| **Preguntas asimétricas** | Misma decisión semántica (`decision_key`, `option_id`) con distinto copy por rol, sexo o perspectiva. |
| **Mismatch declarativo** | Las consecuencias de desacuerdo entre pareja son acciones/outcomes en el contenido, no reglas hardcodeadas en el engine. |
| **Múltiples outcomes** | Pueden aplicar varios outcomes cuyo `when` se cumple en el mismo evento. |
| **Preguntas condicionales** | Diseño preparado; implementación diferida a V2. |

---

## 3. Estructura de un evento

### 3.1 Esquema conceptual

```text
EventDefinition
 ├── id, decision_key
 ├── tags[]                    # clasificación flexible (§4)
 ├── eligibility               # ConditionExpr — cuándo entra al pool (§5)
 ├── presentation              # title_key, preamble_key, description_key
 ├── questions[]               # QuestionDefinition (§7)
 ├── outcomes[]                # OutcomeDefinition — pueden aplicar varios (§9)
 ├── default_actions[]         # ActionTemplate si ningún outcome aplica (§9.4)
 ├── mismatch_actions[]        # ActionTemplate por defecto si hay mismatch (§9.5)
 ├── weight, max_occurrences
 └── couple_only, life_stage   # filtros adicionales opcionales
```

### 3.2 Ejemplo JSON (esqueleto)

```json
{
  "id": "buy_house_finances_60",
  "decision_key": "buy_house",
  "tags": ["financial", "housing", "major_decision"],
  "title_key": "events.buy_house.title",
  "preamble_key": "events.buy_house.preamble",
  "eligibility": {
    "type": "all",
    "items": [
      {"type": "compare", "target": "state", "variable": "finances", "op": "gte", "value": 40},
      {"type": "compare", "target": "state", "variable": "age", "op": "gte", "value": 25}
    ]
  },
  "questions": [ "..." ],
  "outcomes": [ "..." ],
  "weight": 1.0,
  "max_occurrences": 1
}
```

Sin bloque `eligibility` (o con `"type": "all", "items": []`) → el evento aplica en cualquier momento (sujeto solo a `max_occurrences` y selección del engine).

---

## 4. Tags (en lugar de tipo fijo)

En V1 **no** se introduce un campo `event_type` obligatorio. En su lugar, **tags** acordados entre contenido y backend.

**Vocabulario inicial (cerrado en principio, pocos tags):**

| Tag | Uso típico |
|-----|------------|
| `preference` | Gustos, valores — alimenta AnswerBank |
| `decision` | Decisiones con consecuencias fuertes en stats |
| `financial` | Dinero, compras, deudas |
| `housing` | Casa, mudanza, arriendo |
| `relationship` | Pareja, conflicto, intimidad |
| `family` | Hijos, mascotas |
| `career` | Trabajo, estudios |

**Validación V1:** ninguna. Si un tag no está en el vocabulario conocido, se trata como **inexistente** (no falla la carga). Las condiciones del engine usan el target `tag` con semántica «¿este evento tiene el tag X?» (§5.3).

**Futuro:** el backend puede validar contra un enum `EventTag` al persistir contenido.

---

## 5. Evaluador de condiciones

### 5.1 Recomendación: árbol de expresiones (`ConditionExpr`)

**No** usar una librería externa (JSON Logic, CEL) en V1. El paquete `couple_simulator_engine` implementa un evaluador propio, pequeño y sin dependencias:

```text
ConditionExpr
 ├── CompareCondition     # hoja: comparar variable con valor
 ├── AllCondition         # AND  — todas las hijas true
 ├── AnyCondition         # OR   — al menos una hija true
 └── NotCondition         # NOT  — niega una hija
```

Cada nodo es un objeto JSON con discriminador `type`:

```json
{
  "type": "any",
  "items": [
    {
      "type": "all",
      "items": [
        {"type": "compare", "target": "state", "variable": "finances", "op": "gte", "value": 60},
        {"type": "compare", "target": "state", "variable": "children", "op": "gte", "value": 1}
      ]
    },
    {"type": "compare", "target": "event_var", "variable": "home_desire", "op": "gte", "value": 4}
  ]
}
```

### 5.2 Por qué este enfoque

| Criterio | Árbol propio | JSON Logic / CEL |
|----------|--------------|------------------|
| Dependencias | Ninguna | Externa |
| Tests | Casos unitarios claros | Acoplado a librería |
| AND/OR/NOT | Explícito | Sí |
| Extensión (ANSWER, MODE) | Añadir targets al contexto | Posible pero más opaco |
| Legibilidad para autores de contenido | Buena con ejemplos | Curva de aprendizaje |

### 5.3 API del evaluador

```python
@dataclass
class EvaluationContext:
    state: SimulationState
    event_variables: dict[str, Any]
    answers: dict[str, str]          # question_id → option_id (efectivas tras conflicto)
    answers_by_player: dict[str, dict[str, str]]  # player_role → question_id → option_id
    mode: GameMode
    tags: frozenset[str]
    flags: EvaluationFlags           # answers_match, has_mismatch, mismatch_questions, …

def evaluate(expr: ConditionExpr | None, ctx: EvaluationContext) -> bool:
    """None o all vacío → True."""
```

**Targets** en hojas `compare`:

| `target` | Lee de |
|----------|--------|
| `state` | `SimulationState` (finances, age, …) |
| `event_var` | Variables acumuladas en el evento actual |
| `answer` | `answers[variable]` donde `variable` es `question_id` |
| `mode` | `mode == value` |
| `tag` | `value in ctx.tags` — «¿el evento tiene este tag?» |
| `flag` | Flags de evaluación: `answers_match`, `has_mismatch`, `mismatch_on_question` (variable = question_id) |

**Operadores:** `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `in`.

### 5.4 Compatibilidad V1

Una lista plana `[Condition, …]` del diseño anterior equivale a:

```json
{"type": "all", "items": [ ... ]}
```

---

## 6. Preguntas

### 6.1 Estructura

```text
QuestionDefinition
 ├── id
 ├── decision_key          # hereda del evento si se omite; enlaza AnswerBank y conflictos
 ├── order
 ├── text                  # TextPresentation (§6.2)
 ├── options[]
 ├── show_when             # ConditionExpr | null — V2: pregunta condicional
 └── required              # default true
```

### 6.2 Presentación de texto (`TextPresentation`)

Las claves i18n **no desaparecen**: el contenido sigue referenciando `*_key`. Lo que se añade es un mapa de **`params`** (variables de interpolación) que el engine rellena al presentar o al materializar acciones (§6.4).

```json
{
  "default_key": "events.gift.question.default",
  "by_role": {
    "partner_a": "events.gift.what_would_you_like_to_receive",
    "partner_b": "events.gift.what_would_you_give"
  },
  "by_sex": {
    "male": "events.gift.question_male",
    "female": "events.gift.question_female"
  }
}
```

**Resolución de clave (orden sugerido):**

1. `by_role[player_role]` si existe  
2. else `by_sex[player_sex]` si existe  
3. else `default_key`

Misma estructura en preguntas y opciones. `option_id` sigue siendo **semántico y compartido** entre roles y sexos.

### 6.3 Preguntas asimétricas (ejemplo regalo)

```json
{
  "id": "gift_choice",
  "decision_key": "gift_exchange",
  "order": 1,
  "text": {
    "default_key": "events.gift.question.default",
    "by_role": {
      "partner_a": "events.gift.what_would_you_like_to_receive",
      "partner_b": "events.gift.what_would_you_give"
    }
  },
  "options": [
    {
      "id": "flowers",
      "text": {
        "default_key": "events.gift.options.flowers",
        "by_role": {
          "partner_a": "events.gift.options.flowers_as_receiver",
          "partner_b": "events.gift.options.flowers_as_giver"
        }
      }
    }
  ]
}
```

### 6.4 Interpolación de variables en textos

**Las claves i18n no cambian de naturaleza.** Los archivos de locale usan placeholders estándar (p. ej. ICU / `{{name}}` en react-i18next). El engine **no traduce**; provee `params` estructurados para que el frontend (o el adaptador) llame `t(key, params)`.

```json
{
  "type": "show_narrative",
  "payload": {
    "text_key": "events.vacation.narrative.conflict",
    "params": {
      "partner_a_name": "María",
      "partner_b_name": "Carlos",
      "chosen_option_key": "events.options.beach",
      "chosen_option_id": "beach"
    }
  }
}
```

En `es.json`:

```json
{
  "events.vacation.narrative.conflict": "{{partner_b_name}} quiso ir a la playa, pero {{partner_a_name}} prefería la montaña."
}
```

**Quién provee cada param:**

| Param | Origen típico |
|-------|----------------|
| `partner_a_name`, `partner_b_name` | Backend / `LoadedGame` (datos de jugadores) |
| `chosen_option_id` | Respuesta efectiva tras conflicto |
| `chosen_option_key` | Clave i18n de la opción (para reutilizar copy) |
| `stat_name`, `delta` | Action `modify_stat` ya resuelta |

El engine declara en la plantilla **qué params necesita** (`param_refs`); el materializador los resuelve desde `EvaluationContext` + jugadores.

```json
{
  "type": "show_narrative",
  "payload": {
    "text_key": "events.buy_house.narrative.success",
    "param_refs": {
      "partner_a_name": "player.partner_a.name",
      "finances_after": "state.finances"
    }
  }
}
```

### 6.5 Preguntas condicionales (V2 — diseño anticipado)

Ejemplo: «¿Quieren un perro?» → si `yes` → «¿Cómo lo llaman?»

```json
{
  "id": "dog_name",
  "order": 2,
  "show_when": {
    "type": "compare",
    "target": "answer",
    "variable": "want_dog",
    "op": "eq",
    "value": "yes"
  },
  "text": {"default_key": "events.dog.name_question"},
  "options": [ "..." ]
}
```

En V1 todas las preguntas del evento se muestran en orden. En V2 el engine filtra con `show_when` antes de `present_event`. El campo puede existir en el esquema desde ya, ignorado hasta entonces.

---

## 7. Opciones y efectos inmediatos

Cada **opción** puede declarar efectos inmediatos y/o un **`weighted_pick`** (§9.6) con ramas probabilísticas visibles en UI antes de elegir (como «Seguir el plan» 60% / 40%):

```json
{
  "id": "follow_plan",
  "text": {"default_key": "events.diet.options.follow_plan"},
  "effects": [],
  "weighted_pick": {
    "branches": [
      {
        "weight": 60,
        "preview": {"label_key": "events.diet.preview.ovr_up", "stat": "career", "delta": 3},
        "effects": [{"target": "state", "variable": "career", "value": 3}],
        "actions": [{"type": "show_narrative", "payload": {"text_key": "events.diet.success"}}]
      },
      {
        "weight": 40,
        "preview": {"label_key": "events.diet.preview.ovr_down", "stat": "career", "delta": -2},
        "effects": [{"target": "state", "variable": "career", "value": -2}],
        "actions": [{"type": "show_narrative", "payload": {"text_key": "events.diet.failure"}}]
      }
    ]
  }
}
```

```json
{
  "id": "keep_diet",
  "text": {"default_key": "events.diet.options.keep"},
  "effects": [],
  "actions": [{"type": "show_narrative", "payload": {"text_key": "events.diet.no_change"}}]
}
```

| `target` (en `effects`) | Efecto |
|----------|--------|
| `event_var` | Acumula señal interna del evento (se descarta al cerrar) |
| `state` | Modifica `SimulationState` de inmediato (engine = fuente de verdad) |

Los efectos pueden llevar **`distribution`** (§10). El `weighted_pick` se resuelve **al elegir la opción**, con la semilla de la run.

---

## 8. Outcomes y acciones: dos capas

### 8.1 Problema

¿Dónde definir las consecuencias?

| Enfoque | Pros | Contras |
|---------|------|---------|
| **A) Solo outcomes a nivel evento** | Máxima flexibilidad; condiciones compuestas | Verboso para casos simples |
| **B) Solo acciones por opción** | Muy declarativo | Difícil expresar «si Q1=A y Q2=B entonces…» |
| **C) Híbrido (recomendado)** | Opciones acumulan; outcomes deciden el resultado narrativo y stats finales | Dos lugares que aprender |

### 8.2 Decisión: modelo híbrido + múltiples outcomes

```text
Por cada respuesta elegida:
  → aplicar option.effects
  → si option.weighted_pick: elegir rama y aplicar sus effects/actions

Al cerrar todas las preguntas del evento:
  → evaluar TODOS los outcomes cuyo when (ConditionExpr) es true
  → por cada outcome aplicado: effects + materializar actions
  → si hubo mismatch en pareja: evaluar outcomes con flag has_mismatch
       + aplicar event.mismatch_actions (default declarativo)
  → si ningún outcome aplicó: materializar event.default_actions
```

- **Opción:** señales locales, `weighted_pick`, o acciones directas.
- **Outcome:** paquetes condicionados (pueden **acumularse** varios en un mismo evento).
- **No** hay un único «outcome ganador» por orden; todos los que cumplen `when` se aplican.

### 8.3 OutcomeDefinition

```json
{
  "id": "buy_house_success",
  "name_key": "events.buy_house.outcomes.success",
  "order": 1,
  "when": {
    "type": "all",
    "items": [
      {"type": "compare", "target": "event_var", "variable": "home_desire", "op": "gte", "value": 4},
      {"type": "compare", "target": "event_var", "variable": "home_budget", "op": "gte", "value": 2}
    ]
  },
  "effects": [
    {"target": "state", "variable": "finances", "value": -15},
    {"target": "state", "variable": "quality_of_life", "value": 10}
  ],
  "actions": [
    {"type": "add_timeline_entry", "payload": {"title_key": "...", "category": "housing"}},
    {"type": "show_narrative", "payload": {"text_key": "events.buy_house.narrative.success"}}
  ]
}
```

### 8.4 Acciones por defecto del evento (`default_actions`)

Si **ningún outcome** cumple su `when`, el engine materializa `default_actions[]` del evento (lista declarativa de `ActionTemplate`). No hace falta un outcome catch-all con `when: null`.

```json
{
  "id": "vacation_destination",
  "default_actions": [
    {"type": "show_narrative", "payload": {"text_key": "events.vacation.narrative.neutral"}}
  ],
  "outcomes": [ "..." ]
}
```

### 8.5 Mismatch declarativo (no regla transversal)

Las consecuencias de desacuerdo entre pareja se definen **en el contenido**, igual que cualquier otra acción:

1. **Outcomes con condición de mismatch** — p. ej. `when: { "type": "compare", "target": "flag", "variable": "has_mismatch", "op": "eq", "value": true }` o por pregunta con `mismatch_on_question`.
2. **`mismatch_actions[]` en el evento** — plantillas por defecto si hubo mismatch y ningún outcome específico lo cubrió.

```json
{
  "id": "vacation_destination",
  "mismatch_actions": [
    {
      "type": "modify_stat",
      "payload": {"variable": "compatibility", "value": -5}
    },
    {
      "type": "show_narrative",
      "payload": {
        "text_key": "events.vacation.narrative.mismatch_default",
        "param_refs": {
          "partner_a_name": "player.partner_a.name",
          "partner_b_name": "player.partner_b.name"
        }
      }
    }
  ],
  "outcomes": [
    {
      "id": "conflict_beach_vs_mountain",
      "when": {
        "type": "compare",
        "target": "flag",
        "variable": "mismatch_on_question",
        "op": "eq",
        "value": "destination"
      },
      "actions": [
        {"type": "show_narrative", "payload": {"text_key": "events.vacation.conflict.specific"}}
      ]
    }
  ]
}
```

El engine sigue resolviendo **qué opción gana** el conflicto (`ConflictResolver` 65/35), pero las **consecuencias narrativas y de stats** salen de plantillas, no de código fijo. Se puede eliminar la penalización transversal de `GameConfig` si todo queda en contenido.

---

## 9. Acciones: plantilla vs resuelta

### 9.1 Catálogo cerrado de tipos (`ActionType`)

| Tipo | Propósito |
|------|-----------|
| `modify_stat` | Cambio en un stat (payload incluye `variable`, `delta`, `new_value`) |
| `show_narrative` | Texto cerca de avatares / feedback (`text_key` + `params`) |
| `add_timeline_entry` | Entrada en línea de tiempo |
| `update_avatar_hint` | Sugerencia visual de avatar |
| `advance_life_stage` | Cambio de etapa |
| `end_game` | Fin de partida |
| `one_of` | Ocurre **una** de varias sub-acciones según peso (§9.6) |

El contenido solo usa estos tipos en `ActionTemplate`. Tipos nuevos = cambio de versión del engine.

### 9.6 `one_of` — selección probabilística de acciones

Equivalente a «ocurre una de las siguientes acciones». Inspirado en UI de simulación deportiva (p. ej. plan de alimentación: 60% +3 / 40% −2).

**Como `ActionTemplate`:**

```json
{
  "type": "one_of",
  "payload": {
    "branches": [
      {
        "weight": 60,
        "preview": {"label_key": "events.diet.preview.positive", "stat": "career", "delta": 3},
        "actions": [
          {"type": "modify_stat", "payload": {"variable": "career", "value": 3}},
          {"type": "show_narrative", "payload": {"text_key": "events.diet.success"}}
        ]
      },
      {
        "weight": 40,
        "preview": {"label_key": "events.diet.preview.negative", "stat": "career", "delta": -2},
        "actions": [
          {"type": "modify_stat", "payload": {"variable": "career", "value": -2}},
          {"type": "show_narrative", "payload": {"text_key": "events.diet.failure"}}
        ]
      }
    ]
  }
}
```

**En opción (`weighted_pick`):** mismo esquema de ramas; el frontend puede mostrar `preview` **antes** de que el jugador elija (como en la imagen de referencia). Al confirmar la opción, el engine elige rama y materializa.

**Salida del engine:** lista plana de `Action` ya resueltas (sin `one_of` anidado en la respuesta HTTP). El tipo `one_of` solo existe en contenido/plantillas.

**`preview`:** solo para presentación en UI al elegir; no se persiste como acción.

### 9.2 ActionTemplate (en contenido)

Lo que declara el autor del evento:

```json
{
  "type": "modify_stat",
  "payload": {
    "variable": "finances",
    "value": {
      "distribution": {"kind": "uniform", "params": {"min": 5, "max": 15}}
    }
  }
}
```

```json
{
  "type": "show_narrative",
  "payload": {
    "text_key": "events.casino.win",
    "params": {"amount_tier": "medium"}
  }
}
```

### 9.3 Action (salida del engine)

Tras `ActionMaterializer` + RNG:

```json
{
  "type": "modify_stat",
  "payload": {
    "variable": "finances",
    "delta": 12,
    "new_value": 62
  }
}
```

El frontend **nunca** interpreta distribuciones; solo renderiza acciones resueltas.

### 9.4 Pipeline de materialización

```text
Por cada outcome que cumple when (+ mismatch_actions / default_actions si aplica)
  │
  ├─ 1. Aplicar outcome.effects (distribuciones → valores concretos)
  ├─ 2. Por cada ActionTemplate (incl. one_of → expandir a una rama):
  │       resolver param_refs y distributions
  │       generar Action[] con payload final
  └─ 3. Concatenar todas las Action en orden de aplicación
```

Ejemplo casino / dieta: la opción `follow_plan` lleva `weighted_pick`; al elegirla el engine resuelve `one_of` internamente y devuelve `modify_stat` + `show_narrative` concretos.

---

## 10. Distribuciones en efectos y acciones

```json
{
  "target": "state",
  "variable": "compatibility",
  "distribution": {
    "kind": "normal",
    "params": {"median": 10, "std": 3, "clamp_min": 0, "clamp_max": 100}
  }
}
```

| `kind` | Uso |
|--------|-----|
| `fixed` | Valor literal en `value` |
| `uniform` | Entero aleatorio entre min/max |
| `normal` | Muestreo gaussiano; clamp al rango del stat |

El engine usa la semilla de la run (`SeededRNG`) para reproducibilidad.

---

## 11. Flujo completo de un evento

```text
1. eligibility (ConditionExpr)     → ¿entra en el pool?
2. present_event                   → preguntas + previews de weighted_pick
3. jugador(es) responden
4. por cada respuesta:
     option.effects
     option.weighted_pick (si hay)  → one_of → actions parciales
5. conflicto (pareja, si aplica)   → respuestas efectivas + flags mismatch
6. todos los outcomes con when true:
     effects + actions (templates)
7. si has_mismatch: mismatch_actions del evento (si no cubierto por outcomes)
8. si ningún outcome aplicó: default_actions del evento
9. materializar todas las Action → EventResolution
```

---

## 12. Ejemplo integrado (comprar casa, simplificado)

```json
{
  "id": "buy_house_finances_60",
  "decision_key": "buy_house",
  "tags": ["financial", "housing", "decision"],
  "title_key": "events.buy_house.title",
  "eligibility": {
    "type": "compare",
    "target": "state",
    "variable": "finances",
    "op": "gte",
    "value": 40
  },
  "questions": [
    {
      "id": "want_to_buy",
      "order": 1,
      "text": {"default_key": "events.buy_house.questions.want"},
      "options": [
        {"id": "yes", "effects": [{"target": "event_var", "variable": "home_desire", "value": 3}]},
        {"id": "no", "effects": [{"target": "event_var", "variable": "home_desire", "value": -2}]}
      ]
    },
    {
      "id": "budget_ready",
      "order": 2,
      "text": {"default_key": "events.buy_house.questions.budget"},
      "options": [
        {"id": "yes", "effects": [{"target": "event_var", "variable": "home_budget", "value": 2}]},
        {"id": "no", "effects": [{"target": "event_var", "variable": "home_budget", "value": 0}]}
      ]
    }
  ],
  "outcomes": [
    {
      "id": "purchase",
      "order": 1,
      "when": {
        "type": "all",
        "items": [
          {"type": "compare", "target": "event_var", "variable": "home_desire", "op": "gte", "value": 4},
          {"type": "compare", "target": "event_var", "variable": "home_budget", "op": "gte", "value": 2}
        ]
      },
      "effects": [
        {"target": "state", "variable": "finances", "value": -15},
        {"target": "state", "variable": "quality_of_life", "value": 10}
      ],
      "actions": [
        {"type": "add_timeline_entry", "payload": {"title_key": "events.buy_house.timeline.bought", "category": "housing"}},
        {"type": "show_narrative", "payload": {"text_key": "events.buy_house.narrative.bought"}}
      ]
    },
    {
      "id": "keep_renting",
      "when": {
        "type": "compare",
        "target": "event_var",
        "variable": "home_desire",
        "op": "lt",
        "value": 4
      },
      "effects": [{"target": "state", "variable": "finances", "value": 5}],
      "actions": [
        {"type": "show_narrative", "payload": {"text_key": "events.buy_house.narrative.renting"}}
      ]
    }
  ],
  "default_actions": [
    {"type": "show_narrative", "payload": {"text_key": "events.buy_house.narrative.undecided"}}
  ]
}
```

---

## 13. Preguntas cerradas

### Q1 — Probabilidad / ramas *(2026-08-29)*

**Decisión:** tipo de acción **`one_of`** (y `weighted_pick` en opciones) con ramas `{ weight, preview?, actions[], effects? }`. El engine elige una rama; la UI puede mostrar probabilidades antes de elegir (referencia: plan de alimentación en simulación deportiva).

---

### Q2 — Tags *(2026-08-29)*

**Decisión:** vocabulario cerrado en principio, pocos tags. **Sin validación en V1** — tag desconocido = no existe. Condiciones con `target: tag` («¿evento tiene tag X?»).

---

### Q3 — Texto por rol / sexo *(2026-08-29)*

**Decisión:** `TextPresentation` con `default_key`, `by_role` y **`by_sex`**. Resolución: rol → sexo → default.

---

### Q4 — Outcome por defecto *(2026-08-29)*

**Decisión:** **varios outcomes pueden aplicar** en el mismo evento (todos los `when` true). No hay outcome catch-all obligatorio. Fallback declarativo: **`default_actions[]`** a nivel evento.

---

## 14. Referencias

- [game-engine-design.md](./game-engine-design.md) — motor, modos, AnswerBank, `load_game`
- [couple-simulator-engine-package-skeleton.md](./couple-simulator-engine-package-skeleton.md) — módulos `conditions.py`, `resolution/`
