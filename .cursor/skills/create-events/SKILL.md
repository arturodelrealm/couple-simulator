---
name: create-events
description: >-
  Author packaged engine events (JSON + i18n copy + consequences). Prefer speed
  over tests. Use when adding events, event JSON, event copy, questions,
  options, outcomes, or filling texts/consequences.
---

# Create engine events

Ship **content fast**. JSON + locales. **Do not write tests for events.** Actions are already tested; that is enough. Do not run engine/frontend test or lint targets for event-only work.

For the spanish texts use something informal chilean language always.

## Files

- `couple_simulator_engine/couple_simulator_engine/content/events/{id}.json` — i18n **keys**, not prose
- `frontend/src/locales/es.json` and `en.json` → `events.{id}.*`
- Shape: copy a similar packaged event (loader fields, not spec `title_key` / `target`). Conditions use `path` (`state/finances`, `answers/{qid}`, `event_variables/{name}`).

## Flow

1. Skim **one** similar `content/events/*.json` + its locale block (not the whole catalog).
2. Propose: pitch, 1–2 questions, consequence table, ES then EN.
3. Write JSON + both locales. Nested option keys if two questions share `yes`/`no`.
4. Stop. No event tests, no suite runs.

## Event JSON

`id` = filename snake_case. Keys: `events.{id}.title|description|questions.{qid}|options…|conversations.{n}|timeline.{n}`.

Defaults: `weight` 1.0, `max_occurrences` 1, `use_answer_bank` true. `eligibility` / `life_stage` null unless gated. Option `id`s stable across role/sex. Option `actions` = signals (`set_event_var`); `outcomes[].when` = result; `default_actions` if none match. `mismatch_actions` only for couple disagreement.

Question/option `text`: string key, or `{default_key, by_role?, by_sex?}` if copy differs. Title/description/conversation/timeline: plain keys. Resolve `by_role` → `by_sex` → `default_key`.

Optional: `player_role`, `use_answer_bank: false`. `life_stage`: `youth|adult|elderly`. Tags: reuse (`financial`, `housing`, `career`, `leisure`, `relationship`, `family`, …).

Compare: `{type, path, op, value}` ops `eq|neq|gt|gte|lt|lte|in`. Combine `all`/`any`/`not`.

## Probabilistic outcomes

Use this pattern for chance forks (50/50, 30%, etc.). **Do not search the codebase** — copy this recipe.

**Recipe (3 steps):**

1. **Roll on the option** — `set_event_var` in that option's `actions`, sampling 1–100:

```json
{
  "type": "set_event_var",
  "args": {
    "variable": "illness_roll",
    "value": {
      "distribution": {
        "kind": "uniform",
        "params": { "min": 1, "max": 100 }
      }
    }
  }
}
```

2. **Split outcomes** — one outcome per branch; each `when` is `all` of answer match + roll threshold on `event_variables/{variable}`:

| Chance | Bad branch | Good branch |
|--------|------------|-------------|
| 50% | `lte` 50 | `gt` 50 |
| 30% | `lte` 30 | `gt` 30 |
| 70% | `lte` 70 | `gt` 70 |

3. **Put consequences in outcomes** — stats, timeline, conversations per branch. Deterministic options skip the roll and use a single outcome with only `answers/{qid}`.

**Minimal 50/50 example** (option `risky_choice` on question `what_to_do`):

```json
{
  "id": "risky_choice_bad",
  "when": {
    "type": "all",
    "items": [
      { "type": "compare", "path": "answers/what_to_do", "op": "eq", "value": "risky_choice" },
      { "type": "compare", "path": "event_variables/my_roll", "op": "lte", "value": 50 }
    ]
  },
  "actions": [/* bad branch */]
},
{
  "id": "risky_choice_ok",
  "when": {
    "type": "all",
    "items": [
      { "type": "compare", "path": "answers/what_to_do", "op": "eq", "value": "risky_choice" },
      { "type": "compare", "path": "event_variables/my_roll", "op": "gt", "value": 50 }
    ]
  },
  "actions": [/* good branch */]
}
```

**Canonical events:** `partner_b_headache.json` (50% illness), `work_party_crush_low.json` (30% caught).

**Random stat deltas** (separate from branching): put `distribution` inside `modify_stat` `delta` instead of a fixed number — `uniform` `{min, max}` or `normal` `{median, std}`. Does not pick between outcomes; only varies the delta amount.

## Copy

For the spanish texts use something informal chilean language always.

Chilean informal, couple *nosotros*. *depto, arriendo, pega, lucas, po, cachai* when natural. No Spain/Mexico defaults. Light swearing. EN: informal English, no slang calques. Keys/ids English.

## Consequences

Story first. Prefer existing actions; **if none fit, propose a new action** — do not warp questions/outcomes to force-fit handlers. Propose: `type`, `args`, mutate vs UI-only. Same `{type, args, when?}`. Implement handler only if asked (then test the **action**, not the event).

Handlers: `modify_stat` (`finances|quality_of_life|children|wellness|age|compatibility`), `set_event_var`, `add_conversation` (`speaker`, `text_key`), `add_timeline_entry` (`title_key`, `category`, `description_key?`), `advance_life_stage` (`to`), `end_game` (`reason`), `set_housing` (`place`, `type` apartment|house, `quality` bad|ok|excellent), `set_mascot` (`species`+`name` or `mascot: null`), `set_tag` (`key` no `/`, `value` or null), `update_avatar` (`player` partner_a|partner_b, `attribute`, `value`). No `career`/`adventures`. Real forks; `*_key` never inline copy.

Action args detail: [reference.md](reference.md).
