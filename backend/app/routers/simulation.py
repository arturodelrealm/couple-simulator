from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.responses import ok
from app.schemas.simulation import (
    CurrentEventRead,
    EventPresentationRead,
    QuestionPresentationRead,
    SimulationAnswerRead,
    SimulationRunCreate,
    SimulationRunCreated,
    SimulationRunDetail,
    SimulationRunSummary,
    SimulationStateRead,
    TimelineEntryRead,
)
from app.services.simulation_manager import (
    CurrentEventView,
    SimulationRunView,
    simulation_manager,
)
from app.shared.enums import SimulationRunStatus

router = APIRouter()


def _state_read(state: dict) -> SimulationStateRead:
    return SimulationStateRead.model_validate(state)


def _created_payload(view: SimulationRunView) -> dict:
    return SimulationRunCreated(
        run_id=view.run_id,
        player_role=view.player_role,
        status=view.status,
        state=_state_read(view.state),
        events_played=view.events_played,
    ).model_dump()


def _detail_payload(view: SimulationRunView) -> dict:
    return SimulationRunDetail(
        run_id=view.run_id,
        player_role=view.player_role,
        status=view.status,
        state=_state_read(view.state),
        events_played=view.events_played,
        timeline=[TimelineEntryRead.model_validate(item) for item in view.timeline],
        answers=[SimulationAnswerRead.model_validate(item) for item in view.answers],
        current_event_id=view.current_event_id,
        rng_seed=view.rng_seed,
        run_number=view.run_number,
    ).model_dump()


def _current_event_payload(view: CurrentEventView) -> dict:
    event = EventPresentationRead(
        event_id=view.event["event_id"],
        title=view.event["title"],
        description=view.event.get("description"),
        questions=[
            QuestionPresentationRead.model_validate(question)
            for question in view.event["questions"]
        ],
    )
    return CurrentEventRead(run_id=view.run_id, event=event).model_dump()


@router.post("/{game_id}/simulation/runs", status_code=201)
def start_simulation_run(
    game_id: UUID,
    payload: SimulationRunCreate,
    db: Session = Depends(get_db),
) -> dict:
    view = simulation_manager.start_run(
        db,
        game_id,
        payload.player_role.value,
        seed=payload.seed,
        max_events=payload.max_events,
    )
    return ok(_created_payload(view))


@router.get("/{game_id}/simulation/runs")
def list_simulation_runs(
    game_id: UUID,
    status: SimulationRunStatus | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    result = simulation_manager.list_runs(
        db,
        game_id,
        status=status.value if status is not None else None,
        page=page,
        per_page=per_page,
    )
    items = [
        SimulationRunSummary(
            run_id=item.run_id,
            player_role=item.player_role,
            status=item.status,
            created_at=item.created_at,
            run_number=item.run_number,
        ).model_dump()
        for item in result.items
    ]
    return ok(
        {
            "items": items,
            "pagination": {
                "page": result.page,
                "per_page": result.per_page,
                "total": result.total,
            },
        }
    )


@router.get("/{game_id}/simulation/runs/{run_id}")
def get_simulation_run(
    game_id: UUID,
    run_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    view = simulation_manager.get_run(db, game_id, run_id)
    return ok(_detail_payload(view))


@router.get("/{game_id}/simulation/runs/{run_id}/events/current")
def get_current_event(
    game_id: UUID,
    run_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    view = simulation_manager.get_current_event(db, game_id, run_id)
    return ok(_current_event_payload(view))
