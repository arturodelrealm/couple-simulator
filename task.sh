#!/usr/bin/env bash
# Git Bash task runner (no `make` required)
# Usage: ./task.sh runserver
#        ./task.sh makemigrations "add field"

set -euo pipefail

COMPOSE="docker compose"
MSG="${2:-describe the change}"
BACKEND_DIR="backend"

task="${1:-help}"

case "$task" in
  help)
    echo "Available tasks:"
    echo "  ./task.sh runserver"
    echo "  ./task.sh build-server"
    echo "  ./task.sh migrate"
    echo "  ./task.sh makemigrations 'your message'"
    echo "  ./task.sh lint"
    echo "  ./task.sh format"
    echo "  ./task.sh typecheck"
    echo "  ./task.sh test"
    echo "  ./task.sh pre-commit-install"
    echo "  ./task.sh pre-commit-run"
    echo ""
    echo "PowerShell: .\\tasks.ps1 <task>"
    ;;
  runserver)
    $COMPOSE up --build
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
  lint)
    cd "$BACKEND_DIR" && ruff check .
    ;;
  format)
    cd "$BACKEND_DIR" && ruff format .
    ;;
  typecheck)
    $COMPOSE run --rm --no-deps backend sh -c "pip install -e '.[dev]' -q && mypy app/services app/shared"
    ;;
  test)
    $COMPOSE run --rm --no-deps backend sh -c "pip install -e '.[dev]' -q && pytest"
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
