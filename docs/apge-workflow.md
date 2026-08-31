# APGE workflow (couple-simulator)

Guide for running the **Planner → Generator → Evaluator** loop in this repo using Cursor skills. For product architecture, see [AGENTS.md](../AGENTS.md).

---

## What belongs in the repo vs locally

| Location | Committed? | Purpose |
|----------|------------|---------|
| `docs/specs/` | **Yes** | Product and technical specs (source of truth) |
| `docs/research/` | Optional | APGE research notes (promote to `docs/specs/` when stable) |
| `.cursor/skills/apge_*` | **Yes** | Role instructions for planner / generator / evaluator |
| **`.apge/`** | **No** (gitignored) | Per-run plans, backlogs, reports, logs — local harness workspace only |

Do **not** commit files under `.apge/`. When the planner creates `plan.md`, `backlog.md`, or evaluator reports, they are **session artifacts**, not repository documentation.

---

## Local layout (`.apge/` — gitignored)

Created on demand when you run APGE; never checked in:

```text
.apge/
├── spec/plans/{plan}/          # e.g. plan-001-game-engine-v0
│   ├── plan.md
│   ├── sources/                # pointers to docs/specs/, not copies
│   └── epic-Z/
│       ├── backlog.md
│       ├── status.md
│       └── TASK-X.Y-*.md       # reports / notes (runtime)
└── logs/plans/{plan}/          # execution maps, planner threads
```

**Skills** live in [`.cursor/skills/`](../.cursor/skills/):

| Skill | Role |
|-------|------|
| `apge_planner` | Epics, tasks, `plan.md`, `backlog.md` (writes under `.apge/`) |
| `apge_researcher` | Pre-plan research in `docs/research/` |
| `apge_execution_mapper` | Draft `execution-map.draft.yaml` under `.apge/logs/` |
| `apge_generator` | Implements one `TASK-X.Y` in the codebase |
| `apge_evaluator` | Verifies work; writes reports under `.apge/` (no code fixes) |

**Product input for planning:** [docs/specs/](specs/) (e.g. `game-engine-v0-minimal-design.md`), not a pre-seeded plan in git.

---

## Typical flow

1. **Research (optional)** — `apge_researcher` → `docs/research/*.md`
2. **Plan** — `apge_planner` → creates/updates files under `.apge/spec/plans/{plan}/` (local only)
3. **Execute map (optional)** — `apge_execution_mapper` → `.apge/logs/plans/{plan}/execution-map.draft.yaml`
4. **Generate** — `apge_generator` with `{plan}` + `TASK-X.Y`
5. **Evaluate** — `apge_evaluator` with same task id(s)
6. **Rework** — generator reads `TASK-X.Y-evaluator-report.md` and fixes until PASS

Manual runs in Cursor do not require the external **autonomous-pge** CLI. For automated PE loops, install that tool separately.

---

## Generator verification (this repo)

From the repository root, run Makefile **target names**. Use `make <target>` when `make` is installed; otherwise `./task.sh <target>` (Git Bash) or `.\tasks.ps1 <target>` (PowerShell):

| Area | Target(s) |
|------|-----------|
| Backend | `lint`, `format`, `typecheck`, `test` |
| Rules evaluator | `lint-rules-evaluator`, `test-rules-evaluator` (Docker, Python 3.12) |
| Game engine | `lint-couple-simulator-engine`, `test-couple-simulator-engine` (Docker, Python 3.12) |
| Frontend | `lint-frontend`, `format-check-frontend`; then `cd frontend && npm run build` |

Agents must **not** run database migrations or SQL — tell the operator to run `make makemigrations` / `make migrate` (or `./task.sh` with those names) when models change.
