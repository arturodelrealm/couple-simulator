# AGENTS.md — Couple Life Simulator

Technical guidance for AI agents and contributors. **Read this file before making changes.**

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Local setup, commands, documentation index |
| [docs/development-workflow.md](docs/development-workflow.md) | Step-by-step agent workflow and pre-submit checklist |
| [docs/overview.md](docs/overview.md) | Product context, game flow, current milestone |
| [docs/rest-api-standards.md](docs/rest-api-standards.md) | HTTP API shape, errors, REST conventions |
| [docs/apge-workflow.md](docs/apge-workflow.md) | APGE planner / generator / evaluator loop in this repo |
| [docs/backlog/engineering-baseline-backlog.md](docs/backlog/engineering-baseline-backlog.md) | Engineering baseline audit and improvement backlog |

**Cursor rules** in [`.cursor/rules/`](.cursor/rules/) supplement this file — especially `general.mdc`, `backend.mdc`, `frontend.mdc`, `database.mdc`, `testing.mdc`, and `game-engine.mdc`.

**APGE skills** in [`.cursor/skills/`](.cursor/skills/) (`apge_planner`, `apge_generator`, `apge_evaluator`, `apge_researcher`, `apge_execution_mapper`) orchestrate local plan-driven runs. Plans and PE artifacts live under **`.apge/`** at the repo root (gitignored). Product specs stay in **`docs/specs/`**. See [docs/apge-workflow.md](docs/apge-workflow.md).

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Backend | Python, **FastAPI**, PostgreSQL, SQLAlchemy 2.0, Pydantic v2, Alembic |
| Frontend | React, TypeScript, Vite, CSS or Tailwind CSS |
| Avatars | DiceBear (controlled subset of options only) |
| API | REST |

**Decided:** FastAPI over Django/DRF. Alembic for migrations. No full user-auth system required for V1 (personal/single-event use).

---

## General coding rules

### Language and style

- **All code, identifiers, comments, commit messages, and API field names must be in English.**
- Follow **PEP 8** for Python code (line length, naming, imports, spacing).
- **Ruff** enforces Python style and lint rules; run `make lint` / `make format` before committing.
- Follow consistent TypeScript/React conventions on the frontend.
- **Prefer reusable code.** Extract shared logic into reusable modules instead of duplicating it. If something is module-specific, keep it local; if it will be used in more than one place, put it in a shared directory.

### Internationalization (i18n)

User-facing strings must be translatable. Do not hardcode display text in components or API error messages without going through the i18n layer.

**Backend:** use Python `gettext` (or Babel) for translatable strings.

```python
from gettext import gettext as _

from app.shared.exceptions import AppError

raise AppError("GAME_NOT_FOUND", _("Game not found"), status_code=404)
```

**Frontend:** use an i18n library (e.g. `react-i18next`) with translation keys, not inline user-facing strings.

```tsx
// Good
const { t } = useTranslation();
<h1>{t("game.create.title")}</h1>

// Bad
<h1>Create a new game</h1>
```

- Store translation keys in English.
- Keep copy out of business logic; services should raise domain errors, routers map them to translatable HTTP responses.

**Engine event content:** packaged event JSON (`couple_simulator_engine/.../content/events/`) stores **i18n keys**, not display prose, in `title` / `description` / question and option `text`. Conversation and timeline actions use `text_key` / `title_key` / `description_key`. Spanish and English strings live in `frontend/src/locales/es.json` and `en.json` under `events.<event_id>.*`. The play UI resolves keys with `translateContent` / `t()`; the API does **not** gettext event copy. Default UI locale is Spanish (`frontend/src/i18n.ts` `lng: "es"`). When adding an event, add matching keys in both locale files.

---

## Repository layout

```
couple-simulator/
├── backend/
│   ├── app/
│   │   ├── routers/       # thin HTTP layer
│   │   ├── services/      # business logic
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic v2 request/response models
│   │   ├── repositories/  # data access (optional, if needed)
│   │   └── shared/        # reusable helpers and utilities
│   ├── alembic/           # database migrations
│   └── tests/             # pytest suite
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── services/      # API clients
│       ├── hooks/
│       ├── shared/        # reusable UI and utility code
│       └── locales/       # translation files
├── docs/
│   ├── overview.md                 # product overview
│   ├── development-workflow.md     # agent workflow
│   ├── engineering-baseline-backlog.md
│   └── backlog/
├── README.md                       # setup and commands
└── AGENTS.md
```

Match existing structure before introducing new top-level directories.

---

## Backend conventions

### Architecture

| Layer | Responsibility |
|-------|----------------|
| **Routers** | Parse input, call service, return response. No business rules. |
| **Services** | All business logic, orchestration, and domain rules. |
| **Models** | Database schema only. |
| **Schemas** | API contracts (Pydantic v2). |
| **Shared** | Reusable helpers used across modules. |

### SQLAlchemy 2.0

- Use `Mapped[T]`, `mapped_column`, `select()`, `session.execute()`, `session.scalars()`.
- Do **not** use legacy `session.query()`.
- Prefer **UUID primary keys** on new models.
- **Never call `Base.metadata.create_all()`.** All schema changes go through Alembic.

### Pydantic v2

- Use `model_config = ConfigDict(from_attributes=True)` for ORM serialization.
- Use `model_validate()` / `model_dump()` — not v1 `from_orm()` / `dict()`.

### Async

Use **sync by default**. Switch to async only when there is a concrete need (async DB driver, concurrent I/O-bound external calls). Do not make endpoints async just because it is FastAPI.

### Migrations

Every model change requires an Alembic migration:

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

Review autogenerated migrations before applying.

### Linting and formatting

**Backend (Python):** [Ruff](https://docs.astral.sh/ruff/) for linting and formatting. Config lives in `backend/pyproject.toml` (line length 88, rules `E`, `F`, `I`).

**Git hooks:** [pre-commit](https://pre-commit.com/) runs Ruff plus basic file checks on every commit.

**Task runners:** Makefile target names are the source of truth (`lint`, `test`, `lint-couple-simulator-engine`, …). Use `make <target>` when `make` is installed. On Windows Git Bash without `make`, use **`./task.sh <target>`**; in PowerShell use **`.\tasks.ps1 <target>`**. The names and commands match. Prefer `./task.sh` when `make` is missing rather than skipping quality checks.

One-time setup (from repo root):

```bash
pip install -e "./backend[dev]"
make pre-commit-install
# or: ./task.sh pre-commit-install
```

Day-to-day:

```bash
make lint              # check only  (or ./task.sh lint)
make format            # auto-format
make typecheck         # mypy on app/services and app/shared (Docker)
make test              # backend pytest (Docker)
make lint-rules-evaluator
make test-rules-evaluator
make lint-couple-simulator-engine
make test-couple-simulator-engine
make pre-commit-run    # run all hooks on the full repo (CI-friendly)
```

`typecheck`, `test`, `lint-rules-evaluator`, `test-rules-evaluator`, `lint-couple-simulator-engine`, and `test-couple-simulator-engine` run in Docker with **Python 3.12**. Do not use the host `pip`/`python` for those targets (host Python may be 3.11).

`lint-frontend`, `format-frontend`, `format-check-frontend`, and `build-check-frontend` run in Docker (`frontend` Compose service). Do not use host `npm` for those targets.

Backend tests live in `backend/tests/`. Type checking is incremental: mypy runs on `app/services/` and `app/shared/` only. Run with `make test` / `make typecheck`. Optional local Python 3.12: `pip install -e "./backend[dev]"` then `cd backend && pytest`.

Frontend ESLint and Prettier also run via pre-commit (Compose, same as the Make targets) and `make lint-frontend` / `make format-check-frontend`.

---

## Frontend conventions

- Use TypeScript strictly; avoid `any`.
- Keep pages thin; move logic into hooks and services.
- Reusable UI components go in `shared/` or `components/`.
- API calls go through a dedicated service layer, not inline in components.
- All user-visible text goes through i18n translation keys.
- Prioritize functionality over polish until the core game loop works (see [docs/overview.md](docs/overview.md)).

### Linting and formatting

ESLint (flat config in `frontend/eslint.config.js`) and Prettier (`frontend/prettier.config.js`). From repo root:

```bash
make lint-frontend           # ESLint (Docker)
make format-check-frontend   # Prettier check (Docker)
make format-frontend         # Prettier write (Docker)
make build-check-frontend    # tsc + Vite production build (Docker)
```

---

## Domain model

The system is organized around **events**. An event can contain one or more questions and produces an outcome whose effects modify the simulation state.

```
Game
 ├── Player (role: partner_a | partner_b)
 │    └── avatar_config
 ├── Answers (per player, per question)
 ├── SimulationState
 └── TimelineEvents

Event
 ├── Questions → QuestionOptions → OptionEffects
 └── EventOutcomes → OutcomeConditions + OutcomeEffects
```

**Key technical rules:**

- A player's **answer** and the **simulation outcome** are separate concepts.
- Partner A's answers are stored before Partner B starts the simulation.
- Answers from both players are kept independently so rules can change later without losing data.
- Questions and effects must be **data-driven**, not hardcoded per question.
- V1 compatibility: matching answers increase/maintain compatibility; mismatches reduce it.

### Game statuses

```
CREATED → PLAYER_A_READY → PLAYER_B_PLAYING → FINISHED
```

### Life stages

```
YOUTH   (~20–40)
ADULT   (40–60)
ELDERLY (60+)
```

### Simulation state (initial values)

```json
{
  "age": 22,
  "compatibility": 100,
  "finances": 50,
  "quality_of_life": 50,
  "children": 0
}
```

Stats are typically bounded (e.g. 0–100). Do not over-engineer the simulation engine in V1.

### Avatar config

- Use DiceBear Avataaars with a **small, controlled subset** of options (hair, eyes, clothing, accessories).
- Do not expose the full DiceBear option surface.
- Avatar config is stored in the backend and can evolve per life stage in later milestones.

---

## REST API standards

All HTTP endpoints follow a shared response envelope: successful payloads under `data`, errors under `errors` (each with `code` and `message`). Services raise `AppError`; routers use `ok()` from `app.schemas.responses`.

**Full reference:** [docs/rest-api-standards.md](docs/rest-api-standards.md) — response shapes, status codes, URL naming, pagination, validation, frontend types, and an endpoint checklist.

---

## Implementation principles

1. **Separate content from code.** Events, questions, options, and effects should be addable without changing core logic.
2. **Do not over-design the simulation engine.** Explicit per-option effects are fine for V1.
3. **Prefer reusable code** across backend `shared/`, frontend `shared/`, and service layers.

---

## MVP 0 — technical scope

See [docs/overview.md](docs/overview.md) for the product goal and done criteria.

**Backend:**

- `Game` model with UUID, partner A name, game status, timestamps
- Endpoints: `POST /api/games`, `GET /api/games/{game_id}`, `PATCH /api/games/{game_id}`
- `AvatarConfig` model integrated with DiceBear subset
- Alembic migrations for all models

**Frontend:**

- Create game screen
- Avatar builder with visual option cards and preview
- Confirmation screen showing game ID
- Recover persisted game on reload

---

## Agent checklist

Follow the full workflow in [docs/development-workflow.md](docs/development-workflow.md). Before submitting changes, verify:

- [ ] Read [docs/overview.md](docs/overview.md) for product context
- [ ] Read this file and [docs/development-workflow.md](docs/development-workflow.md)
- [ ] All code and identifiers are in English
- [ ] User-facing strings are translatable (gettext / i18n keys)
- [ ] PEP 8 followed for Python; `make pre-commit-run` (or `./task.sh pre-commit-run`) passes
- [ ] `make test` (or `./task.sh test`) passes when backend behavior changes
- [ ] `make typecheck` (or `./task.sh typecheck`) passes when backend services/shared change
- [ ] `make lint-couple-simulator-engine` and `make test-couple-simulator-engine` pass when the game engine changes (Docker, Python 3.12)
- [ ] Business logic in services, not routers
- [ ] SQLAlchemy 2.0 + Pydantic v2 patterns used
- [ ] UUID primary keys on new models
- [ ] Alembic migration created for model changes; no `create_all()`
- [ ] Reusable logic placed in `shared/` directories
- [ ] Async used only when justified
- [ ] REST responses follow [docs/rest-api-standards.md](docs/rest-api-standards.md)
- [ ] `make lint-frontend` and `make format-check-frontend` pass (frontend changes; or `./task.sh` with the same names)
- [ ] `make build-check-frontend` passes (frontend changes; or `./task.sh build-check-frontend`)
- [ ] Changes align with the current MVP milestone scope
