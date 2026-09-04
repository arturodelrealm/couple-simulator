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


def test_catalog_includes_packaged_events() -> None:
    catalog = load_catalog(package_events_directory())
    ids = {event.id for event in catalog.all_events()}
    assert ids == {
        "adult_content_deal",
        "aunt_pepita_inheritance",
        "buy_luxury_car",
        "buy_mid_range_car",
        "child_activity_signup",
        "couples_therapy_suggestion",
        "entertaining_job_offers",
        "first_baby_gender",
        "friend_who_wont_leave",
        "going_bald",
        "how_well_do_you_know",
        "partner_b_headache",
        "pet_parenting_style",
        "plaza_pet_adoption",
        "separation_closure",
        "separation_reconciliation",
        "sex_toys_exploration",
        "unplanned_pregnancy",
        "upgrade_housing",
        "vacation_week_decision",
        "want_kids_decision",
        "work_party_crush",
    }


def test_play_console_completes_with_piped_answers() -> None:
    stdin = "Alex\n" + ("1\n" * 40)
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
    assert "wellness=" in result.stdout
    assert "housing=Providencia/apartment/ok" in result.stdout
    assert "mascot=none" in result.stdout
