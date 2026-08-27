COMPOSE := docker compose
MSG ?= describe the change
BACKEND_DIR := backend
FRONTEND_DIR := frontend

.PHONY: help runserver build-server build-frontend migrate makemigrations check-migrations \
        lint lint-frontend format format-frontend format-check-frontend \
        typecheck test pre-commit-install pre-commit-run

help:
	@echo "Available targets:"
	@echo "  make runserver           Start db + backend + frontend (build if needed)"
	@echo "  make build-server        Build the backend Docker image"
	@echo "  make build-frontend      Build the frontend Docker image"
	@echo "  make migrate             Apply Alembic migrations (upgrade head)"
	@echo "  make makemigrations      Autogenerate migration (MSG='your message')"
	@echo "  make check-migrations    Verify models match applied migrations"
	@echo "  make lint                Run Ruff linter on backend"
	@echo "  make lint-frontend       Run ESLint on frontend"
	@echo "  make format              Run Ruff formatter on backend"
	@echo "  make format-frontend     Run Prettier on frontend"
	@echo "  make format-check-frontend  Check Prettier formatting on frontend"
	@echo "  make typecheck           Run mypy on backend services and shared"
	@echo "  make test                Run backend pytest suite"
	@echo "  make pre-commit-install  Install git pre-commit hooks"
	@echo "  make pre-commit-run      Run all pre-commit hooks on every file"
	@echo ""
	@echo "Windows without make:"
	@echo "  PowerShell:  .\\tasks.ps1 runserver"
	@echo "  Git Bash:    ./task.sh runserver"
	@echo "  cmd.exe:     tasks.bat runserver"

runserver:
	$(COMPOSE) up --build

build-server:
	$(COMPOSE) build backend

build-frontend:
	$(COMPOSE) build frontend

migrate:
	$(COMPOSE) up -d db
	$(COMPOSE) run --rm backend alembic upgrade head

makemigrations:
	$(COMPOSE) up -d db
	$(COMPOSE) run --rm backend alembic revision --autogenerate -m "$(MSG)"

check-migrations:
	$(COMPOSE) up -d db
	$(COMPOSE) run --rm backend sh -c "alembic upgrade head && alembic check"

lint:
	cd $(BACKEND_DIR) && ruff check .

lint-frontend:
	cd $(FRONTEND_DIR) && npm run lint

format:
	cd $(BACKEND_DIR) && ruff format .

format-frontend:
	cd $(FRONTEND_DIR) && npm run format

format-check-frontend:
	cd $(FRONTEND_DIR) && npm run format:check

typecheck:
	$(COMPOSE) run --rm --no-deps backend sh -c "pip install -e '.[dev]' -q && mypy app/services app/shared"

test:
	$(COMPOSE) run --rm --no-deps backend sh -c "pip install -e '.[dev]' -q && pytest"

pre-commit-install:
	pre-commit install

pre-commit-run:
	pre-commit run --all-files
