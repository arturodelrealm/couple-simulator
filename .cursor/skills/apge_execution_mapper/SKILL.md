---
name: apge-execution-mapper
description: >-
  APGE PE-harness helper: drafts execution-map YAML (planned view) with ordered
  steps and separate generator_model and evaluator_model per TASK-X.Y from
  operator scope and constraints. Use when preparing APGE / autonomous-pge
  execution maps, ordering backlog tasks, or emitting execution-map.draft.yaml
  for operator review before the PE loop runs.
---

# autonomous-pge — Execution mapper (draft execution map)

You **draft** an **execution map** file for a **target workspace** so the operator can review and promote it to an **approved** planned map. You do **not** run the PE harness or modify evaluator reports.

**Canonical spec (paths + full YAML semantics):** `docs/spec/execution-map-v1.md` in the **autonomous-pge** repo (external). The minimum schema below is self-contained for drafts in this workspace.

## When to use

The operator is preparing a **planned** execution map (YAML) for the PE harness. They provide **scope** (tasks/epic), **model preferences**, and optional **constraints**. You emit a **draft** they can edit and save as **`execution-map.planned.yaml`** (or the path their harness uses).

## Normative YAML (planned draft) — self-contained

Your output MUST be valid **YAML 1.2** UTF-8. Use this shape; do not rely on any file under the workspace spec plan tree — paths are workspace-specific and may not exist.

**Required top-level fields**

| Field | Value |
|-------|--------|
| `execution_map_version` | Positive integer (use `1` unless the operator says otherwise). |
| `view` | Must be `planned` for drafts you produce. |
| `plan` | The plan **slug** the operator gives you (directory name under `.apge/spec/plans/{plan}/`). |
| `steps` | Non-empty ordered list of steps (execution order; respect dependencies when the operator supplied them). |

**Each step** MUST include all of:

| Field | Meaning |
|-------|--------|
| `task` | String **`"X.Y"`** matching backlog ids (`TASK-X.Y`). |
| `generator_model` | Non-empty string — model id for the **generator** stage (backend-specific, e.g. Cursor CLI). |
| `evaluator_model` | Non-empty string — model id for the **evaluator** stage. |

Never use a single combined model field — **generator** and **evaluator** are always separate keys.

**Optional top-level keys** (informative; parsers tolerate them):

- `scope` — e.g. `mode: epic | tasks | task` plus `epic`, `tasks`, or `task` as appropriate.
- `notes` — freeform operator comment.

**Example (structure only; replace `my-plan` and models with operator input):**

```yaml
execution_map_version: 1
view: planned
plan: my-plan
scope:
  mode: tasks
  tasks: ["2.1", "2.2"]
steps:
  - task: "2.1"
    generator_model: "Model A"
    evaluator_model: "Model B"
  - task: "2.2"
    generator_model: "Model A"
    evaluator_model: "Model B"
```

If the operator attaches a longer format spec or backlog files, treat those as **authoritative for ordering and task ids**; this section remains the **minimum** schema your YAML must satisfy.

## Suggested output path

Write the draft to:

`.apge/logs/plans/{plan}/execution-map.draft.yaml`

(create parent directories if needed). If the operator specifies another path, use theirs.

**Optional human-review copy** (only if the operator asks): next to an epic backlog is sometimes convenient — e.g. `.apge/spec/plans/{plan}/epic-Z/execution-map.planned.yaml` — but layout varies by workspace; do not assume paths exist without the operator naming them.

## Inputs (operator supplies)

- **`{plan}`** slug — the directory name under **`.apge/spec/plans/`** (the planner assigns **`plan-NNN-<slug>`** with the next **NNN**; see **`.cursor/skills/apge_planner/SKILL.md`**).
- **Scope:** epic number, comma-separated task ids, or pasted backlog / execution-order text.
- **Models:** defaults or per-task overrides (opaque strings as the operator names them).
- Optional: paths or `@` attachments to **`plan.md`**, **`epic-Z/backlog.md`**, or any **`sources/*`** file in **their** workspace — read only what they provide.

## Forbidden

- Claiming the draft is **approved** — only the operator promotes draft → **`execution-map.planned.yaml`** (or equivalent).
- Omitting `generator_model` or `evaluator_model` on any step.
- Writing **`execution-map.effective.yaml`** — effective maps are harness-owned at runtime.

## After drafting

Tell the operator to review the YAML, edit as needed, then promote it to the **approved** planned map path their harness expects (often `.apge/logs/plans/{plan}/execution-map.planned.yaml`, or a path passed via **`--execution-map`**).
