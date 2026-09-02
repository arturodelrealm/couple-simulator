# Deployment

Production stack:

| Component | Platform | Source |
|-----------|----------|--------|
| Frontend | Cloudflare Pages | `frontend/` (Vite static build) |
| API | Fly.io | `backend/` (Docker) |
| Database | External PostgreSQL | Connection via Fly secret |

```text
Browser → Cloudflare Pages (React SPA)
              │
              └── HTTPS → Fly.io API → PostgreSQL
```

Local development still uses Docker Compose (`make runserver`); production paths are separate.

---

## Backend (Fly.io)

### Repository layout

`fly.toml` lives in **`backend/`**, but the Docker image needs the **repo root** as build context (the Dockerfile copies `rules_evaluator`, `couple_simulator_engine`, and `backend/`). Deploy from the repository root:

```bash
fly deploy . --config backend/fly.toml --dockerfile backend/Dockerfile
```

### One-time setup

#### 1. Install CLI and log in

```bash
fly auth login
```

#### 2. Confirm the app

```bash
cd backend
fly status
```

If the app does not exist yet:

```bash
fly launch --no-deploy
```

Use app name `couple-simulator` and your preferred region when prompted.

#### 3. Set secrets

Never commit production credentials.

```bash
cd backend
fly secrets set \
  DATABASE_URL="postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME" \
  CORS_ORIGINS="https://YOUR-PAGES-URL.pages.dev,http://localhost:5173" \
  -a couple-simulator
```

Notes:

- Use **`postgresql+psycopg2://`** (SQLAlchemy). The app normalizes common `postgres://` variants automatically.
- **`CORS_ORIGINS`** must include your Cloudflare Pages URL (and `http://localhost:5173` for local dev). Comma-separated, no trailing slashes.
- `ENVIRONMENT=production` is set in `fly.toml`.

#### 4. First manual deploy

```bash
fly deploy . --config backend/fly.toml --dockerfile backend/Dockerfile
curl https://couple-simulator.fly.dev/health
```

Migrations run via `release_command` in `fly.toml` (`alembic upgrade head`).

#### 5. GitHub Actions deploy token

```bash
fly tokens create deploy -a couple-simulator
```

Add to GitHub **Settings → Secrets → Actions**:

| Name | Value |
|------|--------|
| `FLY_API_TOKEN` | Deploy token |

### Automatic deploy on `main`

1. PR → **CI** (lint, test, migrations).
2. Merge to `main` → **CI** runs again.
3. CI success → **Deploy backend** (`.github/workflows/deploy.yml`) → Fly deploy + migrate.

Enable **branch protection** on `main` so only CI-green code merges.

### Local vs production (backend)

| | Local (Compose) | Production (Fly.io) |
|--|-----------------|---------------------|
| Start script | `start.sh` (reload + migrations) | `start-prod.sh` (uvicorn only) |
| Migrations | On container start | `release_command` on deploy |
| Port | Host `8001` → `8000` | Fly `internal_port = 8000` |

---

## Frontend (Cloudflare Pages)

The frontend is a **static Vite build** served by Cloudflare Pages. The Compose `frontend/Dockerfile` stays dev-only (`npm run dev`); production does not use it.

### Cloudflare Pages settings

Connect the GitHub repo and configure:

| Setting | Value |
|---------|--------|
| Production branch | `main` |
| Root directory | `frontend` |
| Build command | `npm run build` |
| Build output directory | `dist` |
| Node.js version | `22` (also in `frontend/.node-version`) |

### Build environment variable

Set in Cloudflare Pages → **Settings → Environment variables** (Production):

| Name | Value |
|------|--------|
| `VITE_API_BASE_URL` | `https://couple-simulator.fly.dev` |

Vite embeds this at **build time**. After changing it, trigger a new deployment.

Optional: set the same variable for **Preview** deployments if PR previews should call the production API.

### SPA routing

React Router uses client-side routes (`/create`, `/games/:id/avatar`, etc.). `frontend/public/_redirects` is copied into `dist/` so Cloudflare serves `index.html` for all paths:

```text
/*    /index.html   200
```

### Update API CORS

After the first Pages deploy, copy your Pages URL and add it to Fly:

```bash
cd backend
fly secrets set \
  CORS_ORIGINS="https://YOUR-PAGES-URL.pages.dev,http://localhost:5173" \
  -a couple-simulator
```

### Smoke test

1. Open the Pages URL.
2. Create a game → build avatar → confirmation.
3. Refresh on `/games/<id>/avatar` (SPA routing).
4. Browser console: no CORS errors.

### Automatic deploy on `main`

Cloudflare Pages rebuilds when `main` updates (Git integration). No GitHub Actions workflow is required for the frontend if Pages is connected to the repo.

Recommended flow with branch protection:

```text
PR → CI → merge to main → Cloudflare Pages build + Fly backend deploy
```

Preview deployments: Cloudflare builds PR branches automatically; ensure preview env has `VITE_API_BASE_URL` if previews should hit the API.

---

## Troubleshooting

| Symptom | Check |
|---------|--------|
| CORS errors in browser | Fly `CORS_ORIGINS` includes exact Pages origin (scheme + host, no path) |
| API calls go to wrong host | `VITE_API_BASE_URL` in Cloudflare build env; redeploy after changing |
| 404 on refresh deep link | `_redirects` present in `frontend/public/` and in deployed `dist/` |
| Backend deploy fails on migrate | `fly logs`; `DATABASE_URL` and DB network access |
| `/health` fails | Fly `internal_port = 8000` |

Backend commands:

```bash
cd backend
fly status
fly logs
fly secrets list
```

Frontend: Cloudflare dashboard → Pages → your project → Deployments / Functions & logs.
