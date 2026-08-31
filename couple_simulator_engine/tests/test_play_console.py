"""Subprocess smoke test for the console adapter."""

import subprocess
import sys
from pathlib import Path

from couple_simulator_engine.content.catalog import (
    load_catalog,
    package_events_directory,
)

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "play_console.py"


def test_play_console_help() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--seed" in result.stdout
    assert "--max-events" in result.stdout


def test_catalog_includes_five_dummy_events() -> None:
    catalog = load_catalog(package_events_directory())
    ids = {event.id for event in catalog.all_events()}
    assert ids == {
        "weekend_trip",
        "buy_house_light",
        "career_offer",
        "midlife_checkpoint",
        "burnout",
    }


def test_play_console_completes_with_piped_answers() -> None:
    stdin = "Alex\n" + ("1\n" * 20)
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--seed",
            "42",
            "--max-events",
            "3",
        ],
        check=False,
        capture_output=True,
        input=stdin,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "Game summary" in result.stdout
    assert "Events played:" in result.stdout
    assert "Actions:" in result.stdout
    assert "Current stats:" in result.stdout
