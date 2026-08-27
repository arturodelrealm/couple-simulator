## Summary

<!-- What changed and why? Link related docs or issues if helpful. -->

## Checklist

- [ ] **Tests** — added or updated where behavior changed (`make test` / relevant frontend checks)
- [ ] **Database migrations** — model changes include an Alembic migration (`make makemigrations`); destructive changes called out below
- [ ] **Secrets** — no `.env`, credentials, tokens, or production values in this PR
- [ ] **Documentation** — README, AGENTS.md, or `docs/` updated if setup, API, or workflow changed
- [ ] **Deployment** — note if this affects Fly.io, Cloudflare Pages, Docker images, or env vars (N/A for most MVP changes)

## Migration notes

<!-- Required when `backend/app/models/` changed. -->

- [ ] No model/schema changes
- [ ] Migration included and reviewed
- [ ] Destructive migration (drop column/table, data loss) — explain rollback plan:

## How to verify

<!-- Commands reviewers can run locally, e.g. make test, make runserver -->
