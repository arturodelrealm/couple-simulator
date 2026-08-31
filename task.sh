#!/usr/bin/env bash
# Git Bash task runner (no `make` required)
# Usage: ./task.sh runserver
#        ./task.sh makemigrations "add field"

set -euo pipefail

COMPOSE="docker compose"
MSG="${2:-describe the change}"
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
RULES_EVALUATOR_DIR="rules_evaluator"
COUPLE_SIMULATOR_ENGINE_DIR="couple_simulator_engine"

task="${1:-help}"

case "$task" in
  help)
    echo "Available tasks:"
    echo "  ./task.sh runserver"
    echo "  ./task.sh build-server"
    echo "  ./task.sh migrate"
    echo "  ./task.sh makemigrations 'your message'"
    echo "  ./task.sh check-migrations"
    echo "  ./task.sh lint"
    echo "  ./task.sh lint-rules-evaluator"
    echo "  ./task.sh lint-couple-simulator-engine"
    echo "  ./task.sh lint-frontend"
    echo "  ./task.sh format"
    echo "  ./task.sh format-frontend"
    echo "  ./task.sh format-check-frontend"
    echo "  ./task.sh typecheck"
    echo "  ./task.sh test"
    echo "  ./task.sh test-rules-evaluator"
    echo "  ./task.sh test-couple-simulator-engine"
    echo "  ./task.sh pre-commit-install"
    echo "  ./task.sh pre-commit-run"
    echo ""
    echo "PowerShell: .\\tasks.ps1 <task>"
    ;;
  runserver)
    $COMPOSE up
    ;;
  build-server)
    $COMPOSE build backend
    ;;
  migrate)
    $COMPOSE up -d db
    $COMPOSE run --rm backend alembic upgrade head
    ;;
  makemigrations)
    $COMPOSE up -d db
    $COMPOSE run --rm backend alembic revision --autogenerate -m "$MSG"
    ;;
  check-migrations)
    $COMPOSE up -d db
    $COMPOSE run --rm backend sh -c "alembic upgrade head && alembic check"
    ;;
  lint)
    cd "$BACKEND_DIR" && ruff check .
    ;;
  lint-rules-evaluator)
    cd "$RULES_EVALUATOR_DIR" && ruff check .
    ;;
  lint-couple-simulator-engine)
    cd "$COUPLE_SIMULATOR_ENGINE_DIR" && ruff check .
    ;;
  lint-frontend)
    cd "$FRONTEND_DIR" && npm run lint
    ;;
  format)
    cd "$BACKEND_DIR" && ruff format .
    ;;
  format-frontend)
    cd "$FRONTEND_DIR" && npm run format
    ;;
  format-check-frontend)
    cd "$FRONTEND_DIR" && npm run format:check
    ;;
  typecheck)
    $COMPOSE run --rm --no-deps backend sh -c "pip install -e '.[dev]' -q && mypy app/services app/shared"
    ;;
  test)
    $COMPOSE run --rm --no-deps backend sh -c "pip install -e '.[dev]' -q && pytest"
    ;;
  test-rules-evaluator)
    cd "$RULES_EVALUATOR_DIR" && pip install -e ".[dev]" -q && pytest
    ;;
  test-couple-simulator-engine)
    cd "$COUPLE_SIMULATOR_ENGINE_DIR" && pip install -e ".[dev]" -q && pytest
    ;;
  pre-commit-install)
    pre-commit install
    ;;
  pre-commit-run)
    pre-commit run --all-files
    ;;
  *)
    echo "Unknown task: $task" >&2
    echo "Run ./task.sh help" >&2
    exit 1
    ;;
esac
