# Couple Simulator Engine (V0)

In-memory console game engine for Couple Life Simulator. No FastAPI or database.

## Install (from repo root)

```bash
pip install -e "./couple_simulator_engine[dev]"
```

Requires the sibling `rules_evaluator` package (pulled in as an editable path dependency).

## Quality checks (from repo root)

These Makefile / `task.sh` / `tasks.ps1` targets run **Docker** (`python-tools`, Python 3.12). They do not use the host `pip`.

```bash
make lint-couple-simulator-engine
make test-couple-simulator-engine

# or
./task.sh lint-couple-simulator-engine
./task.sh test-couple-simulator-engine
```

## Console play

```bash
python couple_simulator_engine/scripts/play_console.py --help
python couple_simulator_engine/scripts/play_console.py --seed 42 --max-events 5
```
