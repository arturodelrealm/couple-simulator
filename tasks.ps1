# Couple Simulator — task runner (Windows PowerShell)
# Usage: .\tasks.ps1 runserver
#        .\tasks.ps1 makemigrations -Msg "add field"

param(
    [Parameter(Position = 0)]
    [string]$Task = "help",

    [string]$Msg = "describe the change"
)

$ErrorActionPreference = "Stop"

function Run-Compose {
    param([string[]]$Args)
    & docker compose @Args
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

switch ($Task) {
    "help" {
        Write-Host "Available tasks:"
        Write-Host "  .\tasks.ps1 runserver"
        Write-Host "  .\tasks.ps1 build-server"
        Write-Host "  .\tasks.ps1 migrate"
        Write-Host "  .\tasks.ps1 makemigrations -Msg 'your message'"
        Write-Host "  .\tasks.ps1 check-migrations"
        Write-Host "  .\tasks.ps1 lint"
        Write-Host "  .\tasks.ps1 lint-rules-evaluator"
        Write-Host "  .\tasks.ps1 lint-couple-simulator-engine"
        Write-Host "  .\tasks.ps1 lint-frontend"
        Write-Host "  .\tasks.ps1 format"
        Write-Host "  .\tasks.ps1 format-frontend"
        Write-Host "  .\tasks.ps1 format-check-frontend"
        Write-Host "  .\tasks.ps1 typecheck"
        Write-Host "  .\tasks.ps1 test"
        Write-Host "  .\tasks.ps1 test-rules-evaluator"
        Write-Host "  .\tasks.ps1 test-couple-simulator-engine"
        Write-Host "  .\tasks.ps1 pre-commit-install"
        Write-Host "  .\tasks.ps1 pre-commit-run"
        Write-Host ""
        Write-Host "Git Bash (without make): ./task.sh <task>"
    }

    "runserver" {
        Run-Compose @("up", "--build")
    }

    "build-server" {
        Run-Compose @("build", "backend")
    }

    "migrate" {
        Run-Compose @("up", "-d", "db")
        Run-Compose @("run", "--rm", "backend", "alembic", "upgrade", "head")
    }

    "makemigrations" {
        Run-Compose @("up", "-d", "db")
        Run-Compose @(
            "run", "--rm", "backend",
            "alembic", "revision", "--autogenerate", "-m", $Msg
        )
    }

    "check-migrations" {
        Run-Compose @("up", "-d", "db")
        Run-Compose @("run", "--rm", "backend", "sh", "-c", "alembic upgrade head && alembic check")
    }

    "lint" {
        Push-Location backend
        & ruff check .
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
        Pop-Location
    }

    "lint-rules-evaluator" {
        Push-Location rules_evaluator
        & ruff check .
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
        Pop-Location
    }

    "lint-couple-simulator-engine" {
        Push-Location couple_simulator_engine
        & ruff check .
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
        Pop-Location
    }

    "lint-frontend" {
        Push-Location frontend
        & npm run lint
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
        Pop-Location
    }

    "format" {
        Push-Location backend
        & ruff format .
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
        Pop-Location
    }

    "format-frontend" {
        Push-Location frontend
        & npm run format
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
        Pop-Location
    }

    "format-check-frontend" {
        Push-Location frontend
        & npm run format:check
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
        Pop-Location
    }

    "typecheck" {
        Run-Compose @("run", "--rm", "--no-deps", "backend", "sh", "-c", "pip install -e '.[dev]' -q && mypy app/services app/shared")
    }

    "test" {
        Run-Compose @("run", "--rm", "--no-deps", "backend", "sh", "-c", "pip install -e '.[dev]' -q && pytest")
    }

    "test-rules-evaluator" {
        Push-Location rules_evaluator
        & pip install -e ".[dev]" -q
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
        & pytest
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
        Pop-Location
    }

    "test-couple-simulator-engine" {
        Push-Location couple_simulator_engine
        & pip install -e ".[dev]" -q
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
        & pytest
        if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
        Pop-Location
    }

    "pre-commit-install" {
        & pre-commit install
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }

    "pre-commit-run" {
        & pre-commit run --all-files
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }

    default {
        Write-Error "Unknown task: $Task. Run .\tasks.ps1 help"
        exit 1
    }
}
