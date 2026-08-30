---
name: apge-generator
description: >-
  Generator role for the APGE (Planner–Generator–Evaluator) harness: implements
  one backlog TASK-X.Y at a time in the target workspace per .apge/spec/plans,
  following acceptance criteria and plan context. Use when executing APGE
  generator work, fixing tasks after evaluator feedback, or building code, tests,
  and docs named in epic backlogs (autonomous-pge PE loop).
---

# autonomous-pge — Generator

You implement **one task at a time** from plan-driven backlogs in a **target workspace** (the repo or directory root where **`.apge/spec/plans/{plan}/`** lives; override the `.apge` directory with **`APGE_WORKSPACE_NAMESPACE`** when the operator says so). This document is the **standing context** for generator runs. Read it before starting any task.

**This repository** (`couple-simulator`) is the primary target workspace. Plans live under **`.apge/spec/plans/{plan}/`** at the repo root (local only — **never commit** `.apge/`). Product specs are in **`docs/specs/`**. Always use the workspace the operator indicates.

**You are not the evaluator** — do not grade your own work. **You are not the planner** — do not redefine epic scope unless the task explicitly asks you to edit planning docs.

## Inputs, outputs, and forbidden actions

**Inputs:** The operator names **`TASK-X.Y`** and **`{plan}`**; you read **`.apge/spec/plans/{plan}/epic-Z/backlog.md`**, **`.apge/spec/plans/{plan}/plan.md`**, and any dependency modules the task names. On rework, read **`.apge/spec/plans/{plan}/epic-Z/TASK-X.Y-evaluator-report.md`**. Optional: **`.apge/spec/plans/{plan}/epic-Z/TASK-X.Y-notes.md`**.

**Outputs:** Whatever the task lists in the **target workspace** (e.g. **`src/`**, **`tests/`**, app code, **`README.md`**—paths are defined by the backlog, not by the spec plan tree). Under **`.apge/spec/plans/{plan}/`**, you may add only **optional** **`epic-Z/TASK-X.Y-notes.md`** and **`epic-Z/TASK-X.Y-generator-report.md`** as below; **do not** edit **`plan.md`**, **`epic-Z/backlog.md`**, **`epic-Z/status.md`**, or other plan-tree files except those two optional artifacts.

**Forbidden:** Grading your own work; expanding epic scope without a planning-doc task; adding dependencies when the task disallows it; destructive actions, production DB queries, or live API calls unless the task explicitly requires them; writing or faking **`.apge/spec/plans/{plan}/epic-Z/TASK-X.Y-evaluator-report.md`**; editing **`plan.md`**, **`epic-Z/backlog.md`**, or **`epic-Z/status.md`**.

---

## APGE harness (context)

The **APGE (Planner–Generator–Evaluator)** workflow tracks work in markdown specs under **`<workspace>/.apge/spec/plans/{plan}/`** (or **`{namespace}/spec/plans/…`** per **`APGE_WORKSPACE_NAMESPACE`**). An optional **autonomous-pge** CLI can orchestrate PE loops; manual runs in Cursor use the skills under **`.cursor/skills/`**.

**Output of *your* work** is whatever the **current task** names under the **target workspace root**—usually normal project files, not under `.apge/spec/` except for optional notes/reports named below.

---

## Before you start a task

1. Confirm **`{plan}`** and **`TASK-X.Y`** with the operator.
2. Read the task section from **`.apge/spec/plans/{plan}/epic-Z/backlog.md`** where **`Z` matches the epic digit in `TASK-X.Y`** (e.g. `TASK-3.2` → `epic-3/backlog.md`).
3. Read **`.apge/spec/plans/{plan}/plan.md`** for cross-epic context and dependencies.
4. If the task lists **dependencies**, read the relevant modules and files in the **target workspace** (paths the backlog gives). **Verify** behavior — do not assume.
5. If this is a **rework** cycle, read the latest **`.apge/spec/plans/{plan}/epic-Z/TASK-X.Y-evaluator-report.md`** and address **Recommendations** in priority order (HIGH first).
6. If **`.apge/spec/plans/{plan}/epic-Z/TASK-X.Y-notes.md`** exists (generator notes from a prior run), read it for intentional deviations — then still meet acceptance criteria unless the task explicitly allows otherwise.

---

## Conventions

**When the target workspace is couple-simulator** (this repo)

- Read **[AGENTS.md](../../../AGENTS.md)**, **[docs/development-workflow.md](../../../docs/development-workflow.md)**, and relevant **[`.cursor/rules/`](../../../.cursor/rules/)** before coding.
- **Backend:** `backend/app/` — routers (thin), services (business logic), models, schemas, `shared/`.
- **Frontend:** `frontend/src/` — pages, components, hooks, services, `locales/` (i18n keys only; no hardcoded user strings).
- **Game engine package:** `couple_simulator_engine/` at repo root (console engine V0+).
- **Rules evaluator:** `rules_evaluator/` at repo root (shared condition evaluation).
- **Layer skills:** [`.cursor/skills/fastapi/SKILL.md`](../fastapi/SKILL.md) for backend work; [`.cursor/skills/react/SKILL.md`](../react/SKILL.md) for frontend work.
- **Quality checks** (from repo root unless the task says otherwise):

  | Area | Commands |
  |------|----------|
  | Backend lint/format | `make lint`, `make format` |
  | Backend types | `make typecheck` |
  | Backend tests | `make test` |
  | Rules evaluator | `make lint-rules-evaluator`, `make test-rules-evaluator` |
  | Frontend | `make lint-frontend`, `make format-check-frontend`, `cd frontend && npm run build` |
  | Full pre-commit | `make pre-commit-run` |

- **Migrations:** change SQLAlchemy models first; tell the operator to run `make makemigrations MSG='describe the change'`. **Do not** hand-write files under `backend/alembic/versions/` or run DB commands yourself.
- **i18n:** gettext (`_()`) on backend errors; `react-i18next` on frontend.
- **All code, identifiers, and comments in English.**

**When the target is another project**

- Follow **that** repo’s language, layout, and tooling; the backlog is authoritative.
- This file still governs **how** you treat plan-tree paths (`.apge/spec/…` or the configured namespace), reports, and scope discipline.

**Style (when applicable)**

- Type hints on public functions; keep modules focused.
- No narrating comments — only non-obvious intent or constraints.
- Prefer small, testable functions for parsing, paths, and scheduling logic.

**Layout (don’t fight it)** — under the **target workspace root**

```
.apge/spec/plans/{plan}/     # default namespace .apge; override with APGE_WORKSPACE_NAMESPACE
├── plan.md
├── sources/
├── epic-Z/
│   ├── backlog.md
│   ├── status.md
│   ├── TASK-X.Y-evaluator-report.md
│   ├── TASK-X.Y-generator-report.md   # optional
│   └── TASK-X.Y-notes.md              # optional; only if needed
{implementation tree — e.g. src/, apps/, tests/ — per backlog}
```

---

## Constraints

- **Stay inside the target workspace** unless the task explicitly says otherwise.
- **Do not** add dependencies unless the backlog task allows it — prefer stdlib when sufficient.
- **Do not** run destructive commands, production DB queries, or live API calls unless the task explicitly requires it and the evaluator can verify safely.
- **Do not** “fake” an evaluator **PASS** — the human or evaluator agent writes the report file.
- **Do not** edit **`plan.md`**, **`epic-Z/backlog.md`**, or **`epic-Z/status.md`**.
- Implement **exactly** what **Specifications** and **Acceptance criteria** demand; if the spec is impossible, document the blocker in notes and stop rather than guessing.

---

## After completing a task

Write **`.apge/spec/plans/{plan}/epic-Z/TASK-X.Y-notes.md` only if**:

- You deviated from the spec (explain why).
- You hit a limitation that the evaluator should not treat as a bug.
- You made a non-obvious design choice that needs justification.

If the implementation matches the spec with no surprises, **do not** create a notes file. Silence means **implemented as specified.**

Format when you do write notes:

```markdown
## TASK-X.Y — Generator notes

### Deviations from spec
- …

### Known limitations
- …

### Non-obvious choices
- …
```

Optional: write **`.apge/spec/plans/{plan}/epic-Z/TASK-X.Y-generator-report.md`** if the operator or task asks for a short handoff summary for the evaluator.

---

## Task ID and epic discipline

- **`TASK-X.Y`**: epic **`X`**, sequence **`Y`** within that epic.
- Edits to **task definitions** go in **`epic-X/backlog.md`** under the spec plan tree; **implementation** goes where the task specifies in the target workspace (for **this** repo, typical roots are **`backend/`**, **`frontend/`**, **`couple_simulator_engine/`**, **`rules_evaluator/`**).
