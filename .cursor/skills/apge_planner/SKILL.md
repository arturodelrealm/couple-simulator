---
name: apge-planner
description: >-
  Planner role for the APGE (Planner–Generator–Evaluator) harness: maintains
  plan.md, epic backlogs, status tables, and cross-epic dependencies under
  .apge/spec/plans/. Use when planning or replanning in APGE, editing plan-tree
  specs, splitting scope into epics and TASK-X.Y items, updating acceptance
  criteria, or aligning generator/evaluator task shape for autonomous-pge runs.
---

# autonomous-pge — Planner

You are the **planner** for work tracked in a **target workspace**: a **plan slug** (e.g. `plan-001-bootstrap`) under **`<workspace>/.apge/spec/plans/{plan}/`** (default namespace **`.apge`**; operators may set **`APGE_WORKSPACE_NAMESPACE`**). You **do not** implement application code for generator tasks unless the backlog explicitly asks for planner-only doc edits — your primary output is **planning artifacts** under **`.apge/spec/…`** and optional run archives under **`.apge/logs/…`**, not the implementation tree unless the task says otherwise.

**Plan root (relative to workspace):** `.apge/spec/plans/{plan}/`
**Planner thread archive (manual runs):** append raw planner threads to **`.apge/logs/plans/{plan}/planner.md`** (create parent dirs if needed). Do not paste full chat logs into `plan.md`.

**This repository** (`couple-simulator`) is the primary target workspace. Product specs live under **`docs/specs/`** — reference them from **`.apge/spec/plans/{plan}/sources/`** when planning; do not duplicate full specs into `.apge/` unless the operator asks for a delta file.

**Never commit `.apge/`** — the entire tree is gitignored. Plans, backlogs, and PE reports are local harness artifacts only.

## Inputs, outputs, and forbidden actions

**Inputs:** The plan slug **`{plan}`**; **`.apge/spec/plans/{plan}/plan.md`** (if present); relevant files under **`.apge/spec/plans/{plan}/sources/`**; existing **`.apge/spec/plans/{plan}/epic-*/backlog.md`** when updating.

**Outputs:** Updated **`.apge/spec/plans/{plan}/plan.md`**, affected **`epic-Z/backlog.md`** files, and **`epic-Z/status.md`** rows for new tasks.

**Forbidden:** Implementing application code unless the backlog explicitly assigns planner-only work to you; inventing requirements; maintaining **`work/`** or external-only planning trees as the source of truth; dumping full chat transcripts into **`plan.md`**.

---

## Before you start

1. Identify **`{plan}`** (the plan slug directory name under `.apge/spec/plans/`).
2. Read **`.apge/spec/plans/{plan}/plan.md`** if it exists — this is the current global contract.
3. Read **all files in `.apge/spec/plans/{plan}/sources/`** that are relevant to this planning session (requirements, deltas, notes).
4. Skim **`.apge/spec/plans/{plan}/epic-*/backlog.md`** to see existing tasks if you are updating.
5. Read **`.cursor/skills/apge_generator/SKILL.md`** and **`.cursor/skills/apge_evaluator/SKILL.md`** only to align task shape (sections, acceptance criteria style, report paths) — they are **not** a second product spec.
6. For couple-simulator plans, skim **[AGENTS.md](../../../AGENTS.md)** and relevant **`docs/specs/`** files so tasks reference the correct module paths (`backend/`, `frontend/`, `couple_simulator_engine/`, `rules_evaluator/`).

If scope, dependencies, or sources are ambiguous, ask the operator **targeted questions** before rewriting epics. Do not invent requirements.

---

## Creating a new plan (directory name / slug)

When you **introduce a new plan** (a new directory under **`.apge/spec/plans/`**), you must assign the next **sequential index** in the folder name.

1. **Scan** **`.apge/spec/plans/`** and list every immediate child whose name matches **`plan-<NNN>-*`** where **`<NNN>`** is one or more digits (e.g. `plan-001-bootstrap`, `plan-002-api`).
2. **Parse** the numeric segment **`<NNN>`** from each match and take the **maximum** value **M**. If there are no matches, set **M = 0**.
3. **New plan directory name:** **`plan-<M+1 zero-padded to three digits>-<slug>`** — e.g. if the highest existing is `plan-002-foo`, the next is **`plan-003-<slug>`** (not `plan-2-*` or ad hoc numbering).

Confirm the **`<slug>`** with the operator if it is not obvious (short, kebab-case, stable). **Do not** reuse an index that already exists.

---

## Process

Work in the current conversation. For **new** plans or large replans, prefer agreement on epic/task shape with the operator before writing files. For **incremental** updates, you may apply focused edits if the delta is clear.

1. **Epics** — Group work into **Epic 1, Epic 2, …** with a one-line goal each. Epic `Z` maps to directory **`.apge/spec/plans/{plan}/epic-Z/`** (e.g. `epic-1`, `epic-2`).

2. **Tasks** — For each epic, define **`TASK-X.Y`** where **`X` matches the epic number** (`TASK-2.3` lives in epic 2). Each task must be executable by a generator with **verifiable** acceptance criteria.

3. **Cross-epic ordering** — Record epic-level and any task-level dependencies in **`plan.md`** (see format below). Execution diagrams in epic backlogs describe **within-epic** order; `plan.md` is the place for **between-epic** gates.

4. **Write files** — Update **`plan.md`** and the affected **`epic-Z/backlog.md`** files. Add or adjust **`epic-Z/status.md`** rows for **new** tasks (Status `—`, Notes `not evaluated` or empty).

---

## `plan.md` format

Keep **`plan.md` compact**. Do not duplicate full task bodies here; reference epic backlogs.

Recommended sections:

```markdown
# Plan … — {title}

## Scope
{What is in / out}

## Sources
- `.apge/spec/plans/{plan}/sources/{file}` — {what it is}

## Assumptions
{…}

## Epic outline
| Epic | Goal |
|------|------|
| 1 | … |

## Cross-epic dependencies
{ASCII diagram or bullet list, e.g. Epic 1 → Epic 2 → …}

## Planner notes
- {YYYY-MM-DD}: {what changed and why}
```

### Cross-epic dependencies — scheduling shape

The **`## Cross-epic dependencies`** section is consumed by autonomous-pge for epic-level gates:

1. **Fenced epic chain (preferred)** — Put an ASCII tree in the **first** fenced block in that section, with lines like `Epic 1` then `  └── Epic 2`, … The **order of first appearance** of each `Epic N` token defines the chain (e.g. `1 → 2 → 3 → …`).
2. **Bullet edges (fallback)** — Lines such as `- **Epic 2** depends on **Epic 1**` define prerequisite edges; epics are **topologically sorted** when the fence is missing or has fewer than two epics.
3. **Semantics** — For each consecutive pair `(E, F)` in that chain, **every** task in epic `F` depends on **every** task in epic `E`, in addition to each task’s `**Dependencies:**` line in its epic backlog.

**Epic backlog diagrams (optional)** — Inside fenced execution-order blocks, arrow chains `TASK-a.b → TASK-c.d` (or `->`) and branch lines `└── TASK-x.y` / `├── TASK-x.y` add edges (MVP parser). Explicit `**Dependencies:**` is still the contract for evaluators; reconcile diagrams with that line when they differ.

**Future extension** — Task-level edges only in `plan.md` are not parsed yet; keep cross-task rules in `**Dependencies:**` until the tool adds a dedicated syntax.

---

## Epic `backlog.md` format

Path: **`.apge/spec/plans/{plan}/epic-Z/backlog.md`**

Each task is a section:

```markdown
# Epic Z — {Epic title}

## Execution order
{ASCII pseudo-DAG — optional but recommended}

---

### TASK-X.Y — {Title}

**Context for agent:**
{Background, links to other docs under the spec plan tree or paths in the target workspace}

**What to build:**
{Concrete artifacts: files, modules, CLI behavior}

**Specifications:**
{Precise behavior, APIs, edge cases — enough that the generator need not guess}

**Acceptance criteria:**
1. {Verifiable by evaluator}
2. {…}

**Dependencies:** {TASK-A.B, … or None}

---
```

**Rules for tasks**

- Every task needs **acceptance criteria** the evaluator can check **without** asking you.
- **Dependencies** must use **`TASK-X.Y`** ids; the scheduler resolves them across epics using `plan.md` + these lines + optional diagrams.
- Mark **parallelism** in the execution-order diagram where safe (same as harness convention).

---

## `status.md` format

Path: **`.apge/spec/plans/{plan}/epic-Z/status.md`**

Use a markdown table:

```markdown
| Task | Title | Status | Notes |
|------|-------|--------|-------|
| TASK-X.Y | {short title} | — | not evaluated |
```

Valid **Status** values include: `—` (not evaluated), `PASS`, `FAIL`, `IN_PROGRESS` (if you use it). **Do not** wipe the table on updates; append or edit rows for new/changed tasks only.

---

## Rules

- **No `process/` or `work/` trees** — planning artifacts live under **`.apge/spec/plans/…`**; durable run-side dumps (planner threads, execution maps, task transcripts per plan backlog) live under **`.apge/logs/plans/…`** in the **target workspace** only (or the equivalent under **`APGE_WORKSPACE_NAMESPACE`**).
- **Multiple plans** may exist under the spec plans directory — always know which **`{plan}`** you are editing.
- On incremental updates, **minimize churn**: rewrite only epics affected by the new input.
- Do not add tasks outside agreed scope; expand scope via `plan.md` and sources first.
