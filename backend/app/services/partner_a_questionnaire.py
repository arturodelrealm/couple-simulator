from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from couple_simulator_engine.config import DEFAULT_MAX_EVENTS
from couple_simulator_engine.content.definitions import EventDefinition
from couple_simulator_engine.questionnaire import (
    list_partner_a_questionnaire_events,
    present_partner_a_questionnaire_events,
)
from couple_simulator_engine.resolution.event_resolver import (
    AnswerValidationError,
    _validate_answers,
)
from couple_simulator_engine.session import Answer
from couple_simulator_engine.snapshot import run_snapshot_from_session
from sqlalchemy.orm import Session

from app.models.game import Game
from app.models.simulation_answer import SimulationAnswer
from app.models.simulation_run import SimulationRun
from app.services.simulation_manager import (
    _apply_run_snapshot,
    _engine_partner_b_if_complete,
    _event_presentation_to_dict,
    _load_game,
    _next_run_number,
    _partner_a,
    _require_ready_for_start,
    _run_list_sort_key,
    get_engine,
)
from app.services.simulation_mapper import (
    engine_sex_from_player,
    lobby_player_to_engine,
)
from app.shared.enums import PlayerRole, SimulationRunKind, SimulationRunStatus
from app.shared.exceptions import AppError
from app.shared.i18n import translate as _


def get_questionnaire(db: Session, game_id: UUID) -> dict[str, Any]:
    prep = get_or_create_prep_run(db, game_id)
    game = _load_game(db, game_id)
    if game is None:
        raise AppError("GAME_NOT_FOUND", _("Game not found"), status_code=404)
    return _questionnaire_payload(game, prep)


def save_event_answers(
    db: Session,
    game_id: UUID,
    event_id: str,
    answers: Sequence[dict[str, str]],
) -> dict[str, Any]:
    prep = get_or_create_prep_run(db, game_id)
    game = _load_game(db, game_id)
    if game is None:
        raise AppError("GAME_NOT_FOUND", _("Game not found"), status_code=404)
    event = _require_a_eligible_event(event_id)
    engine_answers = [
        Answer(question_id=item["question_id"], option_id=item["option_id"])
        for item in answers
    ]
    try:
        _validate_answers(event, engine_answers)
    except AnswerValidationError as exc:
        raise AppError(
            "INVALID_ANSWERS",
            _("Invalid event answers"),
            status_code=409,
        ) from exc

    _upsert_event_answers(prep, event_id, answers)
    _remove_skipped_event(prep, event_id)
    _sync_prep_completion(game, prep)
    db.commit()
    db.refresh(prep)
    return _event_update_payload(game, prep, event_id)


def skip_event(db: Session, game_id: UUID, event_id: str) -> dict[str, Any]:
    prep = get_or_create_prep_run(db, game_id)
    game = _load_game(db, game_id)
    if game is None:
        raise AppError("GAME_NOT_FOUND", _("Game not found"), status_code=404)
    _require_a_eligible_event(event_id)
    _delete_event_answers(prep, event_id)
    skipped = list(prep.skipped_event_ids or [])
    if event_id not in skipped:
        skipped.append(event_id)
    prep.skipped_event_ids = skipped
    _sync_prep_completion(game, prep)
    db.commit()
    db.refresh(prep)
    return _event_update_payload(game, prep, event_id)


def unskip_event(db: Session, game_id: UUID, event_id: str) -> dict[str, Any]:
    prep = get_or_create_prep_run(db, game_id)
    game = _load_game(db, game_id)
    if game is None:
        raise AppError("GAME_NOT_FOUND", _("Game not found"), status_code=404)
    _require_a_eligible_event(event_id)
    _remove_skipped_event(prep, event_id)
    _sync_prep_completion(game, prep)
    db.commit()
    db.refresh(prep)
    return _event_update_payload(game, prep, event_id)


def get_or_create_prep_run(db: Session, game_id: UUID) -> SimulationRun:
    game = _load_game(db, game_id)
    if game is None:
        raise AppError("GAME_NOT_FOUND", _("Game not found"), status_code=404)
    _require_ready_for_start(game, PlayerRole.PARTNER_A.value)

    existing = _existing_prep_run(game)
    if existing is not None:
        _seed_legacy_answers_if_empty(game, existing)
        db.commit()
        db.refresh(existing)
        return existing

    prep = _create_prep_run(db, game)
    _seed_legacy_answers_if_empty(game, prep)
    db.commit()
    db.refresh(prep)
    return prep


def _existing_prep_run(game: Game) -> SimulationRun | None:
    matches = [
        run
        for run in game.simulation_runs
        if run.player_role == PlayerRole.PARTNER_A.value
        and run.run_kind == SimulationRunKind.QUESTIONNAIRE.value
    ]
    if not matches:
        return None
    matches.sort(key=_run_list_sort_key)
    return matches[0]


def _create_prep_run(db: Session, game: Game) -> SimulationRun:
    engine = get_engine()
    partner_a = _partner_a(game)
    session = engine.new_session(
        lobby_player_to_engine(partner_a),
        partner_b=_engine_partner_b_if_complete(game),
        player_role=PlayerRole.PARTNER_A.value,
        max_events=DEFAULT_MAX_EVENTS,
    )
    run_number = _next_run_number(db, game.id, PlayerRole.PARTNER_A.value)
    now = datetime.now(timezone.utc)
    snapshot = run_snapshot_from_session(
        session,
        player_role="partner_a",
        run_number=run_number,
    )
    orm_run = SimulationRun(
        id=UUID(session.session_id),
        game_id=game.id,
        player_role=PlayerRole.PARTNER_A.value,
        run_kind=SimulationRunKind.QUESTIONNAIRE.value,
        run_number=run_number,
        status=SimulationRunStatus.ACTIVE.value,
        skipped_event_ids=[],
        created_at=now,
        updated_at=now,
    )
    _apply_run_snapshot(orm_run, snapshot)
    orm_run.run_kind = SimulationRunKind.QUESTIONNAIRE.value
    db.add(orm_run)
    db.flush()
    return orm_run


def _seed_legacy_answers_if_empty(game: Game, prep: SimulationRun) -> None:
    if prep.answers:
        return

    simulation_runs = [
        run
        for run in game.simulation_runs
        if run.id != prep.id
        and run.player_role == PlayerRole.PARTNER_A.value
        and run.run_kind == SimulationRunKind.SIMULATION.value
    ]
    simulation_runs.sort(key=_run_list_sort_key)

    last_by_key: dict[tuple[str, str], SimulationAnswer] = {}
    for run in simulation_runs:
        answers = sorted(
            run.answers,
            key=lambda item: (item.sort_index is None, item.sort_index or 0),
        )
        for answer in answers:
            last_by_key[(answer.event_id, answer.question_id)] = answer

    for index, source in enumerate(last_by_key.values()):
        prep.answers.append(
            SimulationAnswer(
                event_id=source.event_id,
                question_id=source.question_id,
                option_id=source.option_id,
                sort_index=index,
            )
        )


def _questionnaire_payload(game: Game, prep: SimulationRun) -> dict[str, Any]:
    engine = get_engine()
    partner_a = _partner_a(game)
    events = list_partner_a_questionnaire_events(engine.catalog)
    presentations = present_partner_a_questionnaire_events(
        engine,
        engine.catalog,
        player_sex=engine_sex_from_player(partner_a.sex),
    )
    answers_by_event = _answers_by_event(prep)
    skipped = set(prep.skipped_event_ids or [])
    items: list[dict[str, Any]] = []
    answered_count = 0
    skipped_count = 0
    for event, presentation in zip(events, presentations, strict=True):
        status, saved_answers = _item_status_and_answers(
            event, skipped, answers_by_event
        )
        if status == "answered":
            answered_count += 1
        elif status == "skipped":
            skipped_count += 1
        items.append(
            {
                "event_id": event.id,
                "presentation": _event_presentation_to_dict(presentation),
                "status": status,
                "saved_answers": saved_answers,
                "avatar_previews": _avatar_previews_for_event(event),
            }
        )
    total = len(items)
    return {
        "items": items,
        "progress": {
            "answered": answered_count,
            "skipped": skipped_count,
            "total": total,
            "complete": answered_count + skipped_count == total,
        },
    }


def _answers_by_event(
    prep: SimulationRun,
) -> dict[str, list[SimulationAnswer]]:
    grouped: dict[str, list[SimulationAnswer]] = defaultdict(list)
    ordered = sorted(
        prep.answers,
        key=lambda item: (item.sort_index is None, item.sort_index or 0),
    )
    for answer in ordered:
        grouped[answer.event_id].append(answer)
    return grouped


def _item_status_and_answers(
    event: EventDefinition,
    skipped: set[str],
    answers_by_event: dict[str, list[SimulationAnswer]],
) -> tuple[str, list[dict[str, str]]]:
    if event.id in skipped:
        return "skipped", []
    event_answers = answers_by_event.get(event.id, [])
    answered_ids = {answer.question_id for answer in event_answers}
    required_ids = {question.id for question in event.questions}
    if required_ids and required_ids <= answered_ids:
        saved = [
            {
                "question_id": answer.question_id,
                "option_id": answer.option_id,
            }
            for answer in event_answers
            if answer.question_id in required_ids
        ]
        return "answered", saved
    return "pending", []


def _avatar_previews_for_event(event: EventDefinition) -> list[dict[str, Any]]:
    previews: list[dict[str, Any]] = []
    for outcome in event.outcomes:
        mapped = _option_eq_from_when(outcome.when)
        if mapped is None:
            continue
        question_id, option_id = mapped
        for action in outcome.actions:
            if action.type != "update_avatar":
                continue
            player = action.args.get("player")
            attribute = action.args.get("attribute")
            value = action.args.get("value")
            if not isinstance(player, str) or not isinstance(attribute, str):
                continue
            if not isinstance(value, (str, int)) or isinstance(value, bool):
                continue
            previews.append(
                {
                    "question_id": question_id,
                    "option_id": option_id,
                    "player": player,
                    "attribute": attribute,
                    "value": value,
                }
            )
    return previews


def _option_eq_from_when(when: dict[str, Any] | None) -> tuple[str, str] | None:
    if when is None or when.get("type") != "compare":
        return None
    path = when.get("path")
    option_id = when.get("value")
    if when.get("op") != "eq" or not isinstance(path, str):
        return None
    if not path.startswith("answers/") or not isinstance(option_id, str):
        return None
    question_id = path.removeprefix("answers/")
    if not question_id:
        return None
    return question_id, option_id


def _require_a_eligible_event(event_id: str) -> EventDefinition:
    engine = get_engine()
    for event in list_partner_a_questionnaire_events(engine.catalog):
        if event.id == event_id:
            return event
    raise AppError("EVENT_NOT_FOUND", _("Event not found"), status_code=404)


def _upsert_event_answers(
    prep: SimulationRun,
    event_id: str,
    answers: Sequence[dict[str, str]],
) -> None:
    existing = {
        (answer.event_id, answer.question_id): answer for answer in prep.answers
    }
    next_index = 0
    if prep.answers:
        indexes = [
            answer.sort_index
            for answer in prep.answers
            if answer.sort_index is not None
        ]
        next_index = (max(indexes) + 1) if indexes else len(prep.answers)
    for item in answers:
        key = (event_id, item["question_id"])
        current = existing.get(key)
        if current is not None:
            current.option_id = item["option_id"]
            continue
        prep.answers.append(
            SimulationAnswer(
                event_id=event_id,
                question_id=item["question_id"],
                option_id=item["option_id"],
                sort_index=next_index,
            )
        )
        next_index += 1


def _delete_event_answers(prep: SimulationRun, event_id: str) -> None:
    prep.answers[:] = [answer for answer in prep.answers if answer.event_id != event_id]


def _remove_skipped_event(prep: SimulationRun, event_id: str) -> None:
    skipped = list(prep.skipped_event_ids or [])
    if event_id not in skipped:
        return
    skipped.remove(event_id)
    prep.skipped_event_ids = skipped


def _sync_prep_completion(game: Game, prep: SimulationRun) -> None:
    payload = _questionnaire_payload(game, prep)
    if payload["progress"]["complete"]:
        prep.status = SimulationRunStatus.FINISHED.value
        prep.end_reason = "questionnaire_complete"
        return
    if prep.end_reason == "questionnaire_complete":
        prep.status = SimulationRunStatus.ACTIVE.value
        prep.end_reason = None


def _event_update_payload(
    game: Game,
    prep: SimulationRun,
    event_id: str,
) -> dict[str, Any]:
    payload = _questionnaire_payload(game, prep)
    item = next(entry for entry in payload["items"] if entry["event_id"] == event_id)
    return {"item": item, "progress": payload["progress"]}
