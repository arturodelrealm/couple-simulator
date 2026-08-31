# Couple Life Simulator

A life-simulation game for couples. **Current milestone: MVP 0 (extended)** — lobby, create/join match by name, Partner A setup (name, sex, avatar), persistence, and recovery after refresh.

## Tech stack

| Layer | Stack |
|-------|--------|
| Backend | Python 3.12, FastAPI, PostgreSQL, SQLAlchemy 2.0, Alembic |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Local dev | Docker Compose |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- Optional: `make` (or use `./task.sh` / `tasks.ps1` on Windows)

## Quick start

1. Copy environment placeholders:

   ```bash
   cp .env.example .env
   ```

2. Start the full stack (PostgreSQL, API, frontend):

   ```bash
   make runserver
   ```

   Windows without `make`:

   ```powershell
   .\tasks.ps1 runserver
   ```

   ```bash
   ./task.sh runserver
   ```

3. Open the app:

   | Service | URL |
   |---------|-----|
   | Frontend | http://localhost:5173 |
   | API | http://localhost:8001/api |
   | Health check | http://localhost:8001/health |

   Default host ports are defined in `docker-compose.yml` (API **8001**, DB **5433**, frontend **5173**).

4. Apply migrations on a fresh database (if the backend did not run them automatically):

   ```bash
   make migrate
   ```

## Common commands

Each row is a Makefile **target**. Equivalent without `make`: `./task.sh <target>` (Git Bash) or `.\tasks.ps1 <target>` (PowerShell).

| Task | Command |
|------|---------|
| Start stack | `make runserver` |
| Apply migrations | `make migrate` |
| Check migration consistency | `make check-migrations` |
| Autogenerate migration | `make makemigrations MSG='describe the change'` |
| Backend lint | `make lint` |
| Backend format | `make format` |
| Backend typecheck | `make typecheck` |
| Backend tests | `make test` |
| Rules evaluator lint / tests | `make lint-rules-evaluator` / `make test-rules-evaluator` |
| Game engine lint / tests | `make lint-couple-simulator-engine` / `make test-couple-simulator-engine` |
| Frontend lint | `make lint-frontend` |
| Frontend format | `make format-frontend` |
| Frontend format check | `make format-check-frontend` |
| Frontend build | `cd frontend && npm run build` |
| Run all pre-commit hooks | `make pre-commit-run` |
| Install pre-commit hooks | `make pre-commit-install` |

One-time dev setup (for git hooks and local frontend lint):

```bash
pip install -e "./backend[dev]"
make pre-commit-install
cd frontend && npm install
```

## Project layout

```text
couple-simulator/
├── backend/          # FastAPI app, models, services, Alembic
├── frontend/         # React UI
├── docs/             # Product and engineering documentation
├── AGENTS.md         # Technical conventions for AI agents and contributors
├── Makefile          # Task shortcuts (also task.sh / tasks.ps1)
└── docker-compose.yml
```

## Documentation

| Document | Purpose |
|----------|---------|
| [AGENTS.md](AGENTS.md) | Architecture, coding conventions, agent checklist |
| [docs/development-workflow.md](docs/development-workflow.md) | Step-by-step workflow for agents and contributors |
| [docs/overview.md](docs/overview.md) | Product goals and current milestone |
| [docs/specs/game-lobby-and-player-a-setup.md](docs/specs/game-lobby-and-player-a-setup.md) | Lobby, match name, and Player A setup (implemented) |
| [docs/rest-api-standards.md](docs/rest-api-standards.md) | HTTP API conventions |
| [docs/backlog/engineering-baseline-backlog.md](docs/backlog/engineering-baseline-backlog.md) | Engineering baseline audit and improvement backlog |
| [docs/deployment.md](docs/deployment.md) | Backend deployment to Fly.io |

**AI agents:** read [AGENTS.md](AGENTS.md) and [docs/development-workflow.md](docs/development-workflow.md) before making substantial changes. Cursor rules in `.cursor/rules/` supplement those docs.

## Configuration

- Root [`.env.example`](.env.example) — database URL, CORS, environment (placeholders only; never commit secrets).
- Frontend [`frontend/.env.example`](frontend/.env.example) — local API proxy; production uses `VITE_API_BASE_URL` in Cloudflare Pages (see [docs/deployment.md](docs/deployment.md)).

## Quality checks (current)

- **Backend:** Ruff lint/format via `make lint`, `make format`, and pre-commit.
- **Backend tests:** pytest via `make test` (runs in Docker with Python 3.12). With a local 3.12 venv: `pip install -e "./backend[dev]"` then `cd backend && pytest`.
- **Backend typecheck:** mypy on `app/services/` and `app/shared/` via `make typecheck`.
- **Frontend:** ESLint + Prettier via `make lint-frontend` and `make format-check-frontend`; TypeScript check in `npm run build`.

**CI:** GitHub Actions runs on pushes to `main` and on pull requests (`.github/workflows/ci.yml`) — backend lint/test/typecheck, frontend lint/build, and migration consistency.

**Deploy:** Backend — after CI passes on `main`, `.github/workflows/deploy.yml` deploys the API to Fly.io. Frontend — Cloudflare Pages builds `frontend/` on pushes to `main`. See [docs/deployment.md](docs/deployment.md) for setup (`FLY_API_TOKEN`, `VITE_API_BASE_URL`, CORS).

## License

Personal project — no license specified yet.
