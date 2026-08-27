COMPOSE := docker compose
MSG ?= describe the change
BACKEND_DIR := backend

.PHONY: help runserver build-server build-frontend migrate makemigrations \
        lint format test pre-commit-install pre-commit-run

help:
	@echo "Available targets:"
	@echo "  make runserver           Start db + backend + frontend (build if needed)"
	@echo "  make build-server        Build the backend Docker image"
	@echo "  make build-frontend      Build the frontend Docker image"
	@echo "  make migrate             Apply Alembic migrations (upgrade head)"
	@echo "  make makemigrations      Autogenerate migration (MSG='your message')"
	@echo "  make lint                Run Ruff linter on backend"
	@echo "  make format              Run Ruff formatter on backend"
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

lint:
	cd $(BACKEND_DIR) && ruff check .

format:
	cd $(BACKEND_DIR) && ruff format .

test:
	$(COMPOSE) run --rm --no-deps backend sh -c "pip install -e '.[dev]' -q && pytest"

pre-commit-install:
	pre-commit install

pre-commit-run:
	pre-commit run --all-files
