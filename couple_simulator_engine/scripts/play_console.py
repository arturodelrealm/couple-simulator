"""Console adapter for a solo V0 session (spec §6.1, §8.9)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from couple_simulator_engine import GameConfig, GameEngine, Player
from couple_simulator_engine.content.catalog import (
    load_catalog,
    package_events_directory,
)
from couple_simulator_engine.enums import PlayerRole, PlayerSex
from couple_simulator_engine.session import (
    Answer,
    ClientAction,
    EventPresentation,
    GameSession,
    GameSummary,
    QuestionPresentation,
)
from couple_simulator_engine.state import SimulationState


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Play Couple Life Simulator (console, solo V0)."
    )
    parser.add_argument("--seed", type=int, default=None, help="RNG seed")
    parser.add_argument(
        "--max-events",
        type=int,
        default=None,
        help="Maximum events in this session (default: 15)",
    )
    return parser.parse_args(argv)


def _read_player_name() -> str:
    while True:
        name = input("Player name: ").strip()
        if name:
            return name
        print("Please enter a name.")


def _prompt_option(question: QuestionPresentation) -> str:
    print(f"\n{question.text}")
    for index, option in enumerate(question.options, start=1):
        print(f"  {index}. {option.text}")
    while True:
        raw = input("Choose option number: ").strip()
        try:
            choice = int(raw)
        except ValueError:
            print("Enter a number from the list.")
            continue
        if 1 <= choice <= len(question.options):
            return question.options[choice - 1].id
        print("Enter a number from the list.")


def _collect_answers(presentation: EventPresentation) -> list[Answer]:
    return [
        Answer(question_id=question.id, option_id=_prompt_option(question))
        for question in presentation.questions
    ]


def _print_client_action(action: ClientAction) -> None:
    print(f"  [{action.type}] {action.args}")


def _household_line(state: SimulationState) -> str:
    housing = state.housing
    if state.mascot is None:
        mascot = "none"
    else:
        mascot = f"{state.mascot.species}/{state.mascot.name}"
    return (
        f"wellness={state.wellness} "
        f"housing={housing.place}/{housing.type.value}/{housing.quality.value} "
        f"mascot={mascot}"
    )


def _print_stats(session: GameSession) -> None:
    state = session.state
    print("Current stats:")
    print(
        f"  age={state.age} compatibility={state.compatibility} "
        f"finances={state.finances} quality_of_life={state.quality_of_life} "
        f"children={state.children} life_stage={state.life_stage.value} "
        f"{_household_line(state)}"
    )


def _print_summary(summary: GameSummary) -> None:
    print("\n=== Game summary ===")
    print(f"Events played: {summary.events_played}")
    print(f"End reason: {summary.end_reason}")
    _print_stats_from_state(summary.final_state)
    if summary.timeline:
        print("Timeline:")
        for entry in summary.timeline:
            extra = f" - {entry.description}" if entry.description else ""
            print(f"  [{entry.age}] {entry.title} ({entry.category}){extra}")


def _print_stats_from_state(state: SimulationState) -> None:
    print(
        "Final stats: "
        f"age={state.age} compatibility={state.compatibility} "
        f"finances={state.finances} quality_of_life={state.quality_of_life} "
        f"children={state.children} life_stage={state.life_stage.value} "
        f"{_household_line(state)}"
    )


def play(engine: GameEngine, player: Player, *, seed: int | None) -> GameSummary:
    session = engine.new_session(player, seed=seed)
    while True:
        end = engine.check_end_conditions(session)
        if end.finished:
            break
        event = engine.select_next_event(session)
        if event is None:
            engine.check_end_conditions(session)
            break
        presentation = engine.present_event(
            event,
            player_role=PlayerRole.PARTNER_A,
            player_sex=player.sex,
        )
        print(f"\n--- {presentation.title} ---")
        if presentation.description:
            print(presentation.description)
        answers = _collect_answers(presentation)
        resolution = engine.submit_answers(session, event, answers)
        print("Actions:")
        if resolution.client_actions:
            for action in resolution.client_actions:
                _print_client_action(action)
        else:
            print("  (none)")
        _print_stats(session)
    return engine.build_summary(session)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    catalog = load_catalog(package_events_directory())
    config = (
        GameConfig(max_events=args.max_events)
        if args.max_events is not None
        else GameConfig()
    )
    engine = GameEngine(catalog, config)
    player = Player(id="solo", name=_read_player_name(), sex=PlayerSex.OTHER)
    summary = play(engine, player, seed=args.seed)
    _print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
