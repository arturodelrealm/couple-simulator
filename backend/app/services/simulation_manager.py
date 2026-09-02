from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any
from uuid import UUID

from couple_simulator_engine.content.catalog import (
    load_catalog,
    package_events_directory,
)
from couple_simulator_engine.engine import GameEngine
from couple_simulator_engine.resolution.event_resolver import AnswerValidationError
from couple_simulator_engine.session import Answer, EventPresentation
from couple_simulator_engine.snapshot import RunSnapshot, run_snapshot_from_session
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.game import Game
from app.models.player import Player
from app.models.simulation_answer import SimulationAnswer
from app.models.simulation_run import SimulationRun
from app.models.timeline_entry import TimelineEntry
from app.services.simulation_mapper import (
    game_snapshot_from_db,
    lobby_player_to_engine,
    public_simulation_state,
    simulation_state_to_dict,
)
from app.shared.enums import GameStatus, PlayerRole, SimulationRunStatus
from app.shared.exceptions import AppError
from app.shared.i18n import translate as _

_LIST_PER_PAGE_CAP = 100
_LIST_PER_PAGE_DEFAULT = 20
_PHASE1_PLAYER_ROLE = PlayerRole.PARTNER_A.value


@dataclass(frozen=True)
class SimulationRunView:
    run_id: UUID
    game_id: UUID
    player_role: str
    status: str
    run_number: int
    events_played: int
    current_event_id: str | None
    rng_seed: int
    max_events: int
    state: dict[str, Any]
    answers: list[dict[str, str]]
    timeline: list[dict[str, Any]]
    created_at: datetime | None


@dataclass(frozen=True)
class SimulationRunSummary:
    run_id: UUID
    player_role: str
    status: str
    created_at: datetime | None
    run_number: int


@dataclass(frozen=True)
class SimulationRunList:
    items: list[SimulationRunSummary]
    page: int
    per_page: int
    total: int


@dataclass(frozen=True)
class CurrentEventView:
    run_id: UUID
    event: dict[str, Any]


@dataclass(frozen=True)
class SubmitAnswersView:
    run_id: UUID
    status: str
    state: dict[str, Any]
    events_played: int
    client_actions: list[dict[str, Any]]
    game_finished: bool


@lru_cache(maxsize=1)
def get_engine() -> GameEngine:
    return GameEngine(load_catalog(package_events_directory()))


class SimulationManager:
    def __init__(self, engine: GameEngine | None = None) -> None:
        self._engine = engine if engine is not None else get_engine()

    def start_run(
        self,
        db: Session,
        game_id: UUID,
        player_role: str,
        seed: int | None = None,
        max_events: int | None = None,
    ) -> SimulationRunView:
        if player_role != _PHASE1_PLAYER_ROLE:
            raise AppError(
                "INVALID_PLAYER_ROLE",
                _("Invalid player role"),
                status_code=400,
            )

        game = _load_game(db, game_id)
        if game is None:
            raise AppError("GAME_NOT_FOUND", _("Game not found"), status_code=404)
        _require_ready_for_start(game)
        partner_a = _partner_a(game)

        engine_player = lobby_player_to_engine(partner_a)
        session = self._engine.new_session(
            engine_player,
            seed=seed,
            max_events=max_events,
        )
        run_number = _next_run_number(db, game_id, player_role)
        now = datetime.now(timezone.utc)
        snapshot = run_snapshot_from_session(
            session,
            player_role="partner_a",
            run_number=run_number,
        )
        orm_run = SimulationRun(
            id=UUID(session.session_id),
            game_id=game.id,
            player_role=player_role,
            run_number=run_number,
            created_at=now,
            updated_at=now,
        )
        _apply_run_snapshot(orm_run, snapshot)
        db.add(orm_run)
        db.commit()
        db.refresh(orm_run)
        return _view_from_orm(orm_run, snapshot)

    def get_run(self, db: Session, game_id: UUID, run_id: UUID) -> SimulationRunView:
        game, orm_run = self._load_game_and_run(db, game_id, run_id)
        loaded = self._engine.load_game(game_snapshot_from_db(game, orm_run))
        exported = self._engine.export_snapshot(loaded)
        return _view_from_orm(orm_run, exported.active_run)

    def list_runs(
        self,
        db: Session,
        game_id: UUID,
        status: str | None = None,
        page: int = 1,
        per_page: int = _LIST_PER_PAGE_DEFAULT,
    ) -> SimulationRunList:
        game = _load_game(db, game_id)
        if game is None:
            raise AppError("GAME_NOT_FOUND", _("Game not found"), status_code=404)

        safe_page = max(page, 1)
        safe_per_page = min(max(per_page, 1), _LIST_PER_PAGE_CAP)

        runs = list(game.simulation_runs)
        if status is not None:
            runs = [run for run in runs if run.status == status]
        runs.sort(key=_run_list_sort_key, reverse=True)
        total = len(runs)
        start = (safe_page - 1) * safe_per_page
        page_rows = runs[start : start + safe_per_page]
        items = [
            SimulationRunSummary(
                run_id=run.id,
                player_role=run.player_role,
                status=run.status,
                created_at=run.created_at,
                run_number=run.run_number,
            )
            for run in page_rows
        ]
        return SimulationRunList(
            items=items,
            page=safe_page,
            per_page=safe_per_page,
            total=total,
        )

    def get_current_event(
        self,
        db: Session,
        game_id: UUID,
        run_id: UUID,
    ) -> CurrentEventView:
        game, orm_run = self._load_game_and_run(db, game_id, run_id)
        if orm_run.status == SimulationRunStatus.FINISHED.value:
            raise AppError(
                "RUN_FINISHED",
                _("This simulation run has finished"),
                status_code=409,
            )

        loaded = self._engine.load_game(game_snapshot_from_db(game, orm_run))
        session = loaded.session
        if session.current_event_id:
            event = self._engine.catalog.get(session.current_event_id)
            if event is None:
                raise AppError(
                    "NO_ELIGIBLE_EVENTS",
                    _("No eligible events remain"),
                    status_code=409,
                )
            presentation = self._engine.present_event(event)
            return CurrentEventView(
                run_id=orm_run.id,
                event=_event_presentation_to_dict(presentation),
            )

        event = self._engine.select_next_event(session)
        if event is None:
            self._engine.check_end_conditions(session)
            exported = self._engine.export_snapshot(loaded)
            _apply_run_snapshot(orm_run, exported.active_run)
            db.commit()
            raise AppError(
                "NO_ELIGIBLE_EVENTS",
                _("No eligible events remain"),
                status_code=409,
            )

        session.current_event_id = event.id
        exported = self._engine.export_snapshot(loaded)
        _apply_run_snapshot(orm_run, exported.active_run)
        db.commit()
        presentation = self._engine.present_event(event)
        return CurrentEventView(
            run_id=orm_run.id,
            event=_event_presentation_to_dict(presentation),
        )

    def submit_answers(
        self,
        db: Session,
        game_id: UUID,
        run_id: UUID,
        event_id: str,
        answers: Sequence[dict[str, str]],
    ) -> SubmitAnswersView:
        game, orm_run = self._load_game_and_run(db, game_id, run_id)
        if orm_run.status == SimulationRunStatus.FINISHED.value:
            raise AppError(
                "RUN_FINISHED",
                _("This simulation run has finished"),
                status_code=409,
            )
        if orm_run.current_event_id != event_id:
            raise AppError(
                "EVENT_MISMATCH",
                _("Event does not match the open event"),
                status_code=409,
            )

        event = self._engine.catalog.get(event_id)
        if event is None:
            raise AppError(
                "EVENT_NOT_FOUND",
                _("Event not found"),
                status_code=404,
            )

        loaded = self._engine.load_game(game_snapshot_from_db(game, orm_run))
        session = loaded.session
        engine_answers = [
            Answer(question_id=item["question_id"], option_id=item["option_id"])
            for item in answers
        ]
        try:
            resolution = self._engine.submit_answers(session, event, engine_answers)
        except AnswerValidationError as exc:
            raise AppError(
                "INVALID_ANSWERS",
                _("Invalid event answers"),
                status_code=409,
            ) from exc

        end = self._engine.check_end_conditions(session)
        exported = self._engine.export_snapshot(loaded)
        _apply_run_snapshot(orm_run, exported.active_run)
        db.commit()

        return SubmitAnswersView(
            run_id=orm_run.id,
            status=exported.active_run.status.value,
            state=public_simulation_state(exported.active_run.state),
            events_played=exported.active_run.events_played,
            client_actions=[
                {"type": action.type, "args": dict(action.args)}
                for action in resolution.client_actions
            ],
            game_finished=resolution.game_finished or end.finished,
        )

    def _load_game_and_run(
        self,
        db: Session,
        game_id: UUID,
        run_id: UUID,
    ) -> tuple[Game, SimulationRun]:
        game = _load_game(db, game_id)
        if game is None:
            raise AppError("GAME_NOT_FOUND", _("Game not found"), status_code=404)
        orm_run = next((run for run in game.simulation_runs if run.id == run_id), None)
        if orm_run is None:
            raise AppError(
                "RUN_NOT_FOUND",
                _("Simulation run not found"),
                status_code=404,
            )
        return game, orm_run


def _event_presentation_to_dict(presentation: EventPresentation) -> dict[str, Any]:
    return {
        "event_id": presentation.event_id,
        "title": presentation.title,
        "description": presentation.description,
        "questions": [
            {
                "id": question.id,
                "text": question.text,
                "options": [
                    {
                        "id": option.id,
                        "text": option.text,
                    }
                    for option in question.options
                ],
            }
            for question in presentation.questions
        ],
    }


def _apply_run_snapshot(orm_run: SimulationRun, snapshot: RunSnapshot) -> None:
    orm_run.status = snapshot.status.value
    orm_run.rng_seed = snapshot.rng_seed
    orm_run.events_played = snapshot.events_played
    orm_run.events_played_ids = list(snapshot.events_played_ids)
    orm_run.current_event_id = snapshot.current_event_id
    orm_run.state_snapshot = simulation_state_to_dict(snapshot.state)
    orm_run.event_variables = dict(snapshot.event_variables)
    orm_run.max_events = snapshot.max_events
    orm_run.end_reason = snapshot.end_reason
    orm_run.player_role = snapshot.player_role
    orm_run.run_number = snapshot.run_number

    orm_run.answers.clear()
    for index, answer in enumerate(snapshot.answers):
        orm_run.answers.append(
            SimulationAnswer(
                event_id=answer.event_id,
                question_id=answer.question_id,
                option_id=answer.option_id,
                sort_index=index,
            )
        )

    orm_run.timeline_entries.clear()
    for index, entry in enumerate(snapshot.timeline):
        orm_run.timeline_entries.append(
            TimelineEntry(
                title=entry.title,
                category=entry.category,
                age=entry.age,
                description=entry.description,
                sort_index=index,
            )
        )


def _view_from_orm(orm_run: SimulationRun, snapshot: RunSnapshot) -> SimulationRunView:
    answers = [
        {
            "event_id": item.event_id,
            "question_id": item.question_id,
            "option_id": item.option_id,
        }
        for item in snapshot.answers
    ]
    timeline = [
        {
            "title": item.title,
            "category": item.category,
            "age": item.age,
            "description": item.description,
        }
        for item in snapshot.timeline
    ]
    return SimulationRunView(
        run_id=orm_run.id,
        game_id=orm_run.game_id,
        player_role=orm_run.player_role,
        status=orm_run.status,
        run_number=orm_run.run_number,
        events_played=snapshot.events_played,
        current_event_id=snapshot.current_event_id,
        rng_seed=snapshot.rng_seed,
        max_events=snapshot.max_events,
        state=public_simulation_state(snapshot.state),
        answers=answers,
        timeline=timeline,
        created_at=orm_run.created_at,
    )


def _load_game(db: Session, game_id: UUID) -> Game | None:
    return db.scalar(
        select(Game)
        .where(Game.id == game_id)
        .options(
            selectinload(Game.players).selectinload(Player.avatar_config),
            selectinload(Game.simulation_runs).selectinload(SimulationRun.answers),
            selectinload(Game.simulation_runs).selectinload(
                SimulationRun.timeline_entries
            ),
        ),
    )


def _partner_a(game: Game) -> Player:
    partner_a = next(
        (
            player
            for player in game.players
            if player.role == PlayerRole.PARTNER_A.value
        ),
        None,
    )
    if partner_a is None:
        raise AppError(
            "INTERNAL_ERROR",
            _("Partner A not found for this game"),
            status_code=500,
        )
    return partner_a


def _require_ready_for_start(game: Game) -> None:
    partner_a = _partner_a(game)
    has_name = partner_a.name is not None and partner_a.name.strip() != ""
    has_avatar = partner_a.avatar_config is not None
    has_sex = partner_a.sex is not None
    if (
        game.status != GameStatus.PLAYER_A_READY.value
        or not has_name
        or not has_avatar
        or not has_sex
    ):
        raise AppError(
            "GAME_NOT_READY",
            _("Game is not ready to start a simulation"),
            status_code=409,
        )


def _run_list_sort_key(run: SimulationRun) -> tuple[datetime, int]:
    created = run.created_at
    if created is None:
        created = datetime.min.replace(tzinfo=timezone.utc)
    elif created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return (created, run.run_number)


def _next_run_number(db: Session, game_id: UUID, player_role: str) -> int:
    current_max = db.scalar(
        select(func.max(SimulationRun.run_number)).where(
            SimulationRun.game_id == game_id,
            SimulationRun.player_role == player_role,
        )
    )
    if current_max is None:
        return 1
    return int(current_max) + 1


simulation_manager = SimulationManager()
