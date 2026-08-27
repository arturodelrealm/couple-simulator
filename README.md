# Couple Life Simulator

A life-simulation game for couples. **Current milestone: MVP 0** — create a game, build Partner A's avatar, persist state, and recover after refresh.

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

| Task | Command |
|------|---------|
| Start stack | `make runserver` |
| Apply migrations | `make migrate` |
| Autogenerate migration | `make makemigrations MSG='describe the change'` |
| Backend lint | `make lint` |
| Backend format | `make format` |
| Run all pre-commit hooks | `make pre-commit-run` |
| Install pre-commit hooks | `make pre-commit-install` |
| Frontend production build | `cd frontend && npm run build` |

One-time backend dev setup (for lint hooks outside Docker):

```bash
pip install -e "./backend[dev]"
make pre-commit-install
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
| [docs/rest-api-standards.md](docs/rest-api-standards.md) | HTTP API conventions |
| [docs/engineering-baseline-backlog.md](docs/engineering-baseline-backlog.md) | Engineering baseline audit and improvement backlog |

**AI agents:** read [AGENTS.md](AGENTS.md) and [docs/development-workflow.md](docs/development-workflow.md) before making substantial changes. Cursor rules in `.cursor/rules/` supplement those docs.

## Configuration

- Root [`.env.example`](.env.example) — database URL, CORS, environment (placeholders only; never commit secrets).
- Frontend [`frontend/.env.example`](frontend/.env.example) — API proxy target for Vite.

## Quality checks (current)

- **Backend:** Ruff lint/format via `make lint`, `make format`, and pre-commit.
- **Frontend:** TypeScript strict mode; `npm run build` runs `tsc` then Vite build.

CI, automated tests, and deployment are tracked in [docs/engineering-baseline-backlog.md](docs/engineering-baseline-backlog.md).

## License

Personal project — no license specified yet.
