# Backend deployment (Fly.io)

This document covers deploying the **FastAPI backend** to Fly.io. The React frontend is deployed separately (local Vite dev server for now; production frontend hosting TBD).

## Architecture

```text
Frontend (local or future host)  →  Fly.io API  →  PostgreSQL (external)
```

| Component | Location |
|-----------|----------|
| API | Fly.io app `couple-simulator` (`backend/fly.toml`) |
| Database | Your existing PostgreSQL instance (not managed by this repo) |
| Migrations | `alembic upgrade head` on each deploy (`release_command`) |

## Repository layout

`fly.toml` lives in **`backend/`**, not the repo root. Fly builds the Docker image from `backend/Dockerfile` when you run deploy from that directory.

```bash
cd backend
fly deploy
```

## One-time Fly.io setup

### 1. Install CLI and log in

```bash
fly auth login
```

### 2. Confirm the app

If you already ran `fly launch` from the repo root, the app `couple-simulator` may exist. Remove the root `fly.toml` (if still present) and use `backend/fly.toml` instead.

From `backend/`:

```bash
fly status
```

If the app does not exist yet:

```bash
cd backend
fly launch --no-deploy
```

Use the existing app name (`couple-simulator`) and region (`gru`) when prompted.

### 3. Set secrets

Never commit production credentials. Set them on the Fly app:

```bash
cd backend
fly secrets set \
  DATABASE_URL="postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME" \
  CORS_ORIGINS="http://localhost:5173" \
  -a couple-simulator
```

Notes:

- Use the **`postgresql+psycopg2://`** form (required by SQLAlchemy). If your provider gives `postgres://` or `postgresql://`, the app normalizes common variants automatically.
- Set `CORS_ORIGINS` to the URL(s) where the frontend will run (comma-separated). Update when you deploy the frontend.
- `ENVIRONMENT=production` is set in `fly.toml`; override with a secret only if needed.

### 4. First manual deploy

```bash
cd backend
fly deploy
fly logs
curl https://couple-simulator.fly.dev/health
```

Expected: HTTP 200 with the standard API envelope (`data.status: ok`).

Migrations run once per deploy via `release_command` in `fly.toml`. Check deploy output for Alembic errors before the new version receives traffic.

### 5. GitHub Actions deploy token

Create a deploy token and add it to GitHub:

```bash
fly tokens create deploy -a couple-simulator
```

In GitHub: **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|------|--------|
| `FLY_API_TOKEN` | Token from the command above |

## Automatic deploy on `main`

Flow:

1. Pull request → **CI** workflow (lint, test, migrations check).
2. Merge to `main` → **CI** runs again on push.
3. When CI succeeds → **Deploy backend** workflow runs (`.github/workflows/deploy.yml`).
4. Fly builds the image, runs `alembic upgrade head`, then rolls out the new machines.

Optional but recommended: enable **branch protection** on `main` so CI must pass before merge.

## Local development vs production

| | Local (Docker Compose) | Production (Fly.io) |
|--|------------------------|---------------------|
| Start script | `scripts/start.sh` (reload + migrations on start) | `scripts/start-prod.sh` (uvicorn only) |
| Migrations | On container start | `release_command` on deploy |
| Port | Host `8001` → container `8000` | Fly `internal_port = 8000` |
| Hot reload | Yes (`--reload`) | No |

Compose overrides the container command for development:

```yaml
command: ["sh", "scripts/start.sh"]
```

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Deploy fails on `release_command` | `fly logs`; verify `DATABASE_URL` and DB network access from Fly |
| `/health` fails | `internal_port` must be `8000`; confirm app listens on `0.0.0.0` |
| DB connection errors | URL driver (`postgresql+psycopg2`), firewall, SSL params from provider |
| CORS errors from frontend | Update `CORS_ORIGINS` secret with the frontend origin |

Useful commands:

```bash
cd backend
fly status
fly logs
fly secrets list
fly ssh console
```

## Frontend (later)

The frontend stays on React + Vite + TypeScript. When you host it (Fly static app, Netlify, etc.), set `VITE_API_BASE_URL` at build time to `https://couple-simulator.fly.dev` and add that frontend URL to `CORS_ORIGINS` on the API.
