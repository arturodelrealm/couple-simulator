# Engineering Baseline Backlog

Audit date: 2026-08-26  
Repository: `couple-simulator` (MVP 0 — game creation, avatar builder, persistence)

This document captures the current engineering baseline and a prioritized backlog. It respects existing tooling and conventions; items are categorized as **healthy**, **needs improvement**, **missing**, **human action required**, or **optional/future**.

---

## A. Executive summary

The repository has a **solid MVP 0 foundation**: FastAPI with a service-layer architecture, SQLAlchemy 2.0, Alembic migrations, Ruff + pre-commit for backend quality, Docker Compose for reproducible local development, and a React/TypeScript frontend with strict TypeScript and i18n.

What is **not yet in place** for a maintainable, agent-friendly baseline:

- **No CI** (no `.github/workflows/` at all)
- **No frontend automated tests** (backend pytest added)
- **No deployment configuration** (target platform: Fly.io)
- **No frontend lint/format tooling** (ESLint, Prettier)
- **No dependency update automation** (Dependabot)
- **No secret scanning or security checks in CI**
- **No game engine yet** (expected — current scope is MVP 0 CRUD only)

The codebase already follows good patterns (thin routers, `AppError` + response envelope, Alembic-only schema changes, agent docs in `AGENTS.md`). The backlog focuses on **closing quality gates and deployment gaps** without replacing working choices.

---

## B. Existing healthy infrastructure

- [x] **FastAPI service-layer architecture** — routers in `backend/app/routers/`, business logic in `backend/app/services/`, models/schemas separated. Healthy for MVP 0.
- [x] **SQLAlchemy 2.0 conventions** — `Mapped`, `mapped_column`, `select()`, no legacy `session.query()`.
- [x] **Alembic migrations** — configured in `backend/alembic/`, initial migration `001_initial_mvp0_models.py` matches MVP 0 models. No `Base.metadata.create_all()` in application code.
- [x] **Backend linting and formatting (Ruff)** — `backend/pyproject.toml` with Ruff; `make lint` / `make format`.
- [x] **Backend pytest** — `backend/tests/` with avatar validation, game service, and API smoke tests; `make test` runs via Docker.
- [x] **Backend mypy (incremental)** — `make typecheck` runs mypy on `app/services/` and `app/shared/` with `disallow_untyped_defs`.
- [x] **Pre-commit hooks (backend)** — `.pre-commit-config.yaml` runs Ruff check/format on `backend/` plus basic file hooks. Preserve this setup.
- [x] **Structured API errors** — `AppError`, global exception handlers, `ok()` envelope per `docs/rest-api-standards.md`.
- [x] **Health endpoint** — `GET /health` in `backend/app/main.py` returns standard envelope.
- [x] **Configuration via environment** — `pydantic-settings` in `backend/app/config.py`; root `.env.example` with placeholders only.
- [x] **Secrets ignored** — `.gitignore` covers `.env`, `.env.local`, `.env.*.local`.
- [x] **Docker Compose local stack** — `docker-compose.yml` with PostgreSQL (healthcheck), backend, frontend; `make runserver` / `./task.sh runserver`.
- [x] **Cross-platform task runners** — `Makefile`, `task.sh`, `tasks.ps1`, `tasks.bat`.
- [x] **Frontend TypeScript strictness** — `strict: true`, `noUnusedLocals`, `noUnusedParameters` in `frontend/tsconfig.json`.
- [x] **Frontend typecheck in build** — `npm run build` runs `tsc && vite build`.
- [x] **npm lockfile** — `frontend/package-lock.json` committed.
- [x] **Frontend i18n** — `react-i18next` with translation keys in `frontend/src/locales/en.json`.
- [x] **Backend i18n pattern** — `gettext` / `_()` used in services and error handlers.
- [x] **Agent documentation** — `AGENTS.md`, `docs/development-workflow.md`, and `README.md` with conventions, workflow, and checklist.
- [x] **Cursor rules** — `general`, `backend`, `frontend`, `database`, `testing`, `game-engine`, plus `no-database-queries` and `no-framework-scaffolding`.
- [x] **Cursor skills** — `.cursor/skills/fastapi/SKILL.md`, `.cursor/skills/react/SKILL.md`.
- [x] **Product and API docs** — `docs/overview.md`, `docs/rest-api-standards.md`.
- [x] **CORS configuration** — environment-driven via `CORS_ORIGINS` setting.
- [x] **Avatar validation** — controlled DiceBear subset validated in `backend/app/shared/avatar_validation.py`.

---

## C. Existing but needing improvement

### Documentation and onboarding

- [x] **Add root `README.md`** — onboarding entry point with setup, commands, ports, and doc links.  
  - **Where:** repository root  
  - **Type:** agent + human  
  - **Depends on:** none

- [ ] **Reconcile product backlog doc with current decisions** — `docs/backlog/backlog_simulador_vida_pareja.md` is largely in Spanish and still lists “FastAPI vs Django” as pending; `AGENTS.md` already records FastAPI + Alembic as decided.  
  - **Where:** `docs/backlog/`  
  - **Type:** agent  
  - **Depends on:** none  
  - **Notes:** Either add an English summary section pointing to `AGENTS.md`, or mark outdated sections explicitly. Avoid duplicating `docs/overview.md`.

### Backend quality gaps (extend, do not replace)

- [x] **Add pytest and initial backend tests** — `game_service`, `avatar_validation`, status transitions, and API smoke tests in `backend/tests/`.  
  - **Where:** `backend/tests/`, `backend/pyproject.toml` `[project.optional-dependencies] dev`  
  - **Type:** agent  
  - **Depends on:** none

- [x] **Add mypy (incremental)** — mypy on `app/services/` and `app/shared/`; `make typecheck` via Docker.  
  - **Where:** `backend/pyproject.toml`, Makefile  
  - **Type:** agent  
  - **Depends on:** none  
  - **Notes:** Extend to routers/models/schemas later; do not block on full-repo coverage.

- [ ] **Add structured application logging** — only Alembic logging is configured. Unhandled exceptions return generic 500 with no server-side log.  
  - **Where:** `backend/app/main.py`, exception handlers  
  - **Type:** agent  
  - **Depends on:** none  
  - **Notes:** Log exception type/message at ERROR in `unhandled_exception_handler`; avoid logging secrets or full request bodies.

- [ ] **Pin or lock Python dependencies** — `pyproject.toml` uses `>=` ranges; no `uv.lock`, `poetry.lock`, or `requirements.lock`. Reproducible CI and deploys benefit from a lockfile.  
  - **Where:** `backend/pyproject.toml` + lock strategy (uv or pip-tools — pick one, do not add overlapping tools)  
  - **Type:** agent proposes, human confirms tool choice if preference exists  
  - **Depends on:** none

### Frontend quality gaps

- [ ] **Add ESLint for React/TypeScript** — no ESLint config or dependency. `AGENTS.md` already anticipates extending pre-commit once frontend lint exists.  
  - **Where:** `frontend/package.json`, ESLint config  
  - **Type:** agent  
  - **Depends on:** none

- [ ] **Add Prettier (optional but recommended)** — no formatter for frontend; backend uses Ruff format.  
  - **Where:** `frontend/`, root or frontend Prettier config  
  - **Type:** agent  
  - **Depends on:** ESLint config (integrate eslint-config-prettier to avoid conflicts)

- [ ] **Extend pre-commit for frontend** — `.pre-commit-config.yaml` covers backend only; `AGENTS.md` line 155 already says to extend it.  
  - **Where:** `.pre-commit-config.yaml`  
  - **Type:** agent  
  - **Depends on:** ESLint (+ Prettier if added)

### Docker and local development

- [ ] **Separate dev vs production backend startup** — `backend/scripts/start.sh` runs `uvicorn ... --reload` (development). Production needs a non-reload entrypoint without bind-mount assumptions.  
  - **Where:** `backend/scripts/`, `backend/Dockerfile`  
  - **Type:** agent prepares; human validates first deploy  
  - **Depends on:** Fly.io deployment task

- [ ] **Production frontend build strategy** — `frontend/Dockerfile` runs Vite dev server (`npm run dev`). Acceptable for local Compose; production should serve static `dist/` (nginx, Caddy, or Fly static + API).  
  - **Where:** `frontend/Dockerfile`, deployment docs  
  - **Type:** agent prepares  
  - **Depends on:** Fly.io deployment task

### Database and migrations

- [ ] **CI migration consistency check** — no automated check that model changes have corresponding migrations.  
  - **Where:** `.github/workflows/` script or Makefile target  
  - **Type:** agent  
  - **Depends on:** CI workflow creation  
  - **Approach:** Run `alembic revision --autogenerate` in CI against ephemeral Postgres; fail if diff is non-empty (or use `alembic check` when available).

- [ ] **Document migration review expectations** — destructive migrations (`drop`, `alter` data loss) should be called out in PRs.  
  - **Where:** PR template + short section in agent workflow doc  
  - **Type:** agent  
  - **Depends on:** PR template

### Health checks

- [ ] **Optional DB-aware health check** — current `/health` does not verify database connectivity. Sufficient for MVP; add `/health/ready` or extend `/health` when deployment needs it.  
  - **Where:** `backend/app/main.py`  
  - **Type:** agent (when deploying)  
  - **Depends on:** Fly.io deployment task  
  - **Notes:** Keep `/health` minimal for liveness; readiness can check DB.

### Security (configuration-level)

- [ ] **Tighten CORS for production** — development allows `allow_methods=["*"]`, `allow_headers=["*"]`. Acceptable locally; production should restrict to known origins and required methods/headers.  
  - **Where:** `backend/app/main.py`, `ENVIRONMENT`-aware settings  
  - **Type:** agent  
  - **Depends on:** production `CORS_ORIGINS` secret (human)

---

## D. Missing

### CI / GitHub Actions (highest impact gap)

No `.github/workflows/` directory exists. CI is the authoritative quality gate.

- [ ] **Create PR CI workflow** — single workflow (avoid duplicates) with jobs:  
  - **Backend:** `make pre-commit-run` or Ruff + pytest + mypy  
  - **Frontend:** ESLint + `npm run build` (includes `tsc`)  
  - **Migration check:** autogenerate diff against ephemeral Postgres  
  - **Permissions:** minimum required (`contents: read`); no `write-all`  
  - **Where:** `.github/workflows/ci.yml`  
  - **Type:** agent  
  - **Depends on:** pytest, ESLint, migration check script

- [ ] **Add Dependabot configuration** — no `dependabot.yml`; no automated dependency PRs for Python, npm, GitHub Actions, or Docker base images.  
  - **Where:** `.github/dependabot.yml`  
  - **Type:** agent  
  - **Depends on:** none  
  - **Notes:** May also require enabling Dependabot in GitHub repo settings (human).

- [ ] **Add secret scanning to CI** — no Gitleaks or equivalent. Evaluate GitHub native secret scanning (Advanced Security if available) vs lightweight Gitleaks action; pick **one**, not both.  
  - **Where:** `.github/workflows/ci.yml` or dedicated security workflow  
  - **Type:** agent proposes; human enables repo-level scanning if needed  
  - **Depends on:** CI workflow

- [ ] **Add dependency vulnerability check** — no `npm audit` or `pip-audit` in CI.  
  - **Where:** CI jobs  
  - **Type:** agent  
  - **Depends on:** CI workflow  
  - **Notes:** Start as informational or fail on high/critical only.

### Testing strategy (game engine — future-critical)

- [ ] **Backend test harness** — pytest configured; extend coverage as game engine grows.  
  - **Where:** `backend/tests/`  
  - **Type:** agent  
  - **Depends on:** game engine implementation (not in MVP 0)

- [ ] **Prioritized test targets (as game engine is built)** — do not chase coverage percentage; test behavior that is expensive to break:  
  - Event resolution  
  - Outcome conditions and effects  
  - Simulation state transitions  
  - Compatibility calculation  
  - Timeline generation  
  - Multi-question events  
  - **Where:** `backend/tests/` (mirror future `app/services/` or `app/engine/`)  
  - **Type:** agent  
  - **Depends on:** game engine implementation (not in MVP 0)

- [ ] **Frontend unit tests (Vitest) — defer until UI logic grows** — hooks and `apiClient` error parsing are reasonable first targets; skip Playwright until core loop exists.  
  - **Where:** `frontend/`  
  - **Type:** agent  
  - **Depends on:** ESLint baseline; optional until post-MVP 0

### Agentic development

- [x] **Agent workflow documentation** — `docs/development-workflow.md` with 13-step workflow, preserve-tooling rule, migration and quality guidance.  
  - **Where:** `docs/development-workflow.md`  
  - **Type:** agent  
  - **Depends on:** none

- [x] **Additional Cursor rules (minimal, non-duplicative)** — `general.mdc`, `backend.mdc`, `frontend.mdc`, `database.mdc`, `testing.mdc`, `game-engine.mdc` supplement `AGENTS.md` and existing rules.  
  - **Where:** `.cursor/rules/`  
  - **Type:** agent  
  - **Depends on:** none

### Branch and PR policy

- [ ] **Pull request template** — none exists. Should cover tests, migrations, secrets, docs, deployment impact.  
  - **Where:** `.github/pull_request_template.md`  
  - **Type:** agent  
  - **Depends on:** none

### Deployment (Fly.io — prepare only)

- [ ] **`fly.toml` for backend API** — not present.  
  - **Where:** repository root or `backend/fly.toml`  
  - **Type:** agent prepares  
  - **Depends on:** human Fly.io app creation

- [ ] **Production Dockerfile for backend** — current Dockerfile is fine for Compose; may need multi-stage or non-reload CMD for Fly.  
  - **Where:** `backend/Dockerfile`  
  - **Type:** agent  
  - **Depends on:** production start script

- [ ] **GitHub Actions deploy workflow** — trigger on merge to `main`: deploy to Fly.io, run migrations, health check.  
  - **Where:** `.github/workflows/deploy.yml`  
  - **Type:** agent prepares  
  - **Depends on:** human secrets and first manual deploy verification

- [ ] **Deployment documentation** — document flow: PR → CI → merge → deploy → migrate → verify.  
  - **Where:** `docs/deployment.md` (new, focused)  
  - **Type:** agent  
  - **Depends on:** Fly.io prep tasks

### Architecture documentation (add only where valuable)

- [ ] **`docs/architecture.md` (lightweight)** — high-level diagram: Frontend → API → Services → Engine → Persistence. Not a duplicate of `AGENTS.md` domain section.  
  - **Where:** `docs/architecture.md`  
  - **Type:** agent  
  - **Depends on:** none  
  - **Optional:** defer if README + AGENTS.md suffice for now.

- [ ] **ADR for FastAPI + Alembic choice** — decision is recorded in `AGENTS.md` but not as an ADR. One short ADR avoids re-litigation by agents.  
  - **Where:** `docs/decisions/001-fastapi-alembic.md`  
  - **Type:** agent  
  - **Priority:** low

### Game engine (product scope, not baseline infra)

- [ ] **Implement data-driven game engine module** — no `resolve_event`, simulation state, or event models yet. MVP 0 is game CRUD + avatar only. This is **product work**, but baseline testing and CI should be ready before engine complexity lands.  
  - **Where:** future `backend/app/services/` or `backend/app/engine/`  
  - **Type:** agent + product backlog  
  - **Depends on:** pytest harness, agent rules for game engine

---

## E. HUMAN ACTION REQUIRED

Do **not** mark these complete unless the user confirms.

### Fly.io and production infrastructure

- [ ] **Fly.io account login** — `fly auth login` on a machine used for deploys.
- [ ] **Create Fly.io application(s)** — backend API app; decide if frontend is static on Fly, separate app, or external host.
- [ ] **Provision PostgreSQL** — Fly Postgres or attached database; obtain production `DATABASE_URL`.
- [ ] **Choose region and resources** — confirm billing/free-tier implications.
- [ ] **Set Fly.io secrets** — `DATABASE_URL`, `ENVIRONMENT=production`, `CORS_ORIGINS` (production frontend URL). Never commit these to Git.
- [ ] **First production deployment** — verify app starts, migrations apply, `/health` responds.
- [ ] **Verify production migration behavior** — confirm `alembic upgrade head` strategy (release command vs startup) before relying on automation.

### GitHub repository settings

- [ ] **Add GitHub Actions secrets** — e.g. `FLY_API_TOKEN` for deploy workflow (after Fly app exists).
- [ ] **Enable Dependabot** — if not auto-enabled after adding `dependabot.yml`.
- [ ] **Enable secret scanning** — GitHub Advanced Security or repository secret scanning settings (if available on account tier).
- [ ] **Configure branch protection on `main`** — require CI passing before merge (optional but recommended once CI exists).

### Local environment (each developer)

- [ ] **Copy `.env.example` to `.env`** — adjust ports/credentials if needed.
- [ ] **Install backend dev dependencies** — `pip install -e "./backend[dev]"` and `make pre-commit-install`.
- [ ] **Run first local stack** — `make runserver` or `./task.sh runserver`; run `make migrate` if DB is fresh.

---

## F. Agent actions

Tasks a coding agent can perform autonomously (after user approves implementation of this backlog):

1. ~~**Write root `README.md`**~~ — done.
2. ~~**Add `docs/development-workflow.md`**~~ — done.
3. ~~**Add pytest + initial tests**~~ — done.
4. ~~**Add mypy** with incremental strictness on services/shared~~ — done.
5. **Add ESLint (+ optional Prettier)** for frontend; extend `.pre-commit-config.yaml`.
6. **Create `.github/workflows/ci.yml`** — backend lint/test/typecheck, frontend lint/build, migration check, minimal permissions.
7. **Create `.github/dependabot.yml`** — Python, npm, GitHub Actions, Docker.
8. **Add `.github/pull_request_template.md`**.
9. **Add migration consistency script** — Makefile target + CI step.
10. **Add structured logging** in exception handlers.
11. ~~**Create focused `.cursor/rules/*.mdc`**~~ — done.
12. **Prepare Fly.io artifacts** — `fly.toml`, production start script, deploy workflow template, `docs/deployment.md`.
13. **Add optional `/health/ready`** with DB ping when deployment work starts.
14. **Update this backlog** — check off items as completed; never mark human tasks done without confirmation.

Agents must **not**:

- Run database migrations or queries against live databases (per `.cursor/rules/no-database-queries.mdc`).
- Hand-write Alembic migration files from scratch (autogenerate via user/`make makemigrations`).
- Replace Ruff, pre-commit, FastAPI, or existing Docker Compose workflow.
- Paste production secrets into source files or Git.
- Pretend to complete Fly.io account or GitHub secret configuration.

---

## G. Recommended implementation order

Adapted to this repository’s actual gaps:

| Phase | Focus | Key deliverables |
|-------|--------|------------------|
| **1** | Repository audit | ✅ This document |
| **2** | Agent instructions | ✅ `README.md`, `docs/development-workflow.md`, Cursor rules |
| **3** | Local quality tooling | ✅ pytest, mypy (services/shared); ESLint, pre-commit frontend extensions remain |
| **4** | CI quality gates | `.github/workflows/ci.yml`, PR template, migration consistency check |
| **5** | Security checks | Dependabot, secret scan (one tool), dependency audit in CI |
| **6** | Database safety | Migration check in CI; document destructive migration review in PR template |
| **7** | Deployment preparation | `fly.toml`, production Dockerfile/start script, deploy workflow **template**, `docs/deployment.md` |
| **8** | Documentation cleanup | Reconcile product backlog doc; optional ADR and architecture doc |

**Defer until game engine work begins:**

- Broad frontend test suite (Vitest)
- E2E tests (Playwright)
- Deep game-engine test matrix (outcomes, timeline, compatibility)

---

## H. Definition of done

The engineering baseline is **complete enough for confident agent-assisted development and simple Fly.io deployment** when all of the following are true:

### Quality gates

- [ ] CI runs on every pull request and is required before merge to `main`.
- [ ] Backend: Ruff (lint + format), pytest (core services covered), mypy on services/shared in CI (local: `make typecheck` ✅).
- [ ] Frontend: ESLint passes; `npm run build` (with `tsc`) passes in CI.
- [ ] Migration consistency check runs in CI when backend models change.

### Security and dependencies

- [ ] `.env*` secrets are gitignored; `.env.example` has placeholders only.
- [ ] Secret scanning runs in CI or is enabled at the GitHub org/repo level.
- [ ] Dependabot (or equivalent) opens update PRs for Python, npm, and GitHub Actions.
- [ ] CI includes a dependency vulnerability step (npm audit / pip-audit) with a documented severity policy.

### Agent and contributor experience

- [x] `README.md` enables a new developer or agent to run the stack locally in one documented path.
- [x] `AGENTS.md` + `docs/development-workflow.md` + focused Cursor rules guide agents without contradicting each other.
- [ ] PR template reminds contributors about tests, migrations, secrets, and deployment.

### Deployment readiness (artifacts prepared; human steps confirmed)

- [ ] `fly.toml`, production backend entrypoint, and deploy workflow exist and are documented.
- [ ] Human has completed Fly.io app, database, secrets, and verified first deploy + migration.
- [ ] `/health` (and readiness check if used) is wired into Fly health checks.

### Explicit non-goals (baseline complete without these)

- Full game engine implementation (product milestone, not infra baseline).
- High test coverage percentages for UI boilerplate.
- Enterprise security stack (WAF, SSO, multi-environment GitFlow).
- Replacing Docker Compose, Ruff, pre-commit, or FastAPI architecture.

---

## Appendix: audit notes

| Area | Finding |
|------|---------|
| **CI** | No GitHub workflows in repo or on `origin/main`. |
| **Tests** | ✅ Backend pytest (16 tests); no frontend tests yet. |
| **README** | ✅ Added — setup, commands, doc index. |
| **Backend deps** | `pyproject.toml` dev extras: pre-commit, ruff, pytest, httpx, mypy. |
| **Frontend deps** | No ESLint, Prettier, Vitest, Playwright. |
| **Game engine** | Not implemented; MVP 0 game/avatar API only. |
| **Logging** | No app-level logging configuration. |
| **Deployment** | No `fly.toml`; backend uses dev `--reload` in `start.sh`. |
| **Health** | `GET /health` exists; no DB check. |
| **Migrations** | Alembic healthy; one initial migration; models imported in `env.py`. |
| **Lockfiles** | `frontend/package-lock.json` yes; Python lockfile no. |
| **Agent docs** | ✅ `AGENTS.md`, `development-workflow.md`, README, 8 Cursor rules. |

---

*Last updated by engineering baseline audit. Update checkboxes as work completes; keep human-action items separate from agent-completed items.*
