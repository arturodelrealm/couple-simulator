from __future__ import annotations

from typing import Any, cast

from couple_simulator_engine.config import GameConfig
from couple_simulator_engine.enums import (
    LifeStage,
    PlayerSex,
    RelationshipStatus,
    SessionStatus,
)
from couple_simulator_engine.player import Player as EnginePlayer
from couple_simulator_engine.session import RecordedAnswer
from couple_simulator_engine.session import (
    TimelineEntry as EngineTimelineEntry,
)
from couple_simulator_engine.snapshot import (
    GameSnapshot,
    PlayerRoleName,
    RunSnapshot,
)
from couple_simulator_engine.state import SimulationState

from app.models.game import Game
from app.models.player import Player
from app.models.simulation_run import SimulationRun
from app.shared.enums import PlayerRole
from app.shared.enums import PlayerSex as BackendPlayerSex
from app.shared.exceptions import AppError
from app.shared.i18n import translate as _

_BACKEND_SEX_TO_ENGINE: dict[str, PlayerSex] = {
    BackendPlayerSex.MALE.value: PlayerSex.MALE,
    BackendPlayerSex.FEMALE.value: PlayerSex.FEMALE,
    BackendPlayerSex.PREFER_NOT_TO_SAY.value: PlayerSex.OTHER,
}


def engine_sex_from_player(sex: str | None) -> PlayerSex:
    if sex is None:
        raise AppError(
            "GAME_NOT_READY",
            _("Game is not ready to start a simulation"),
            status_code=409,
        )
    mapped = _BACKEND_SEX_TO_ENGINE.get(sex)
    if mapped is None:
        raise AppError(
            "INVALID_PLAYER_SEX",
            _("Invalid player sex"),
            status_code=400,
        )
    return mapped


def _avatar_config_as_str_dict(
    config: dict[str, Any] | None,
) -> dict[str, str] | None:
    if config is None:
        return None
    return {str(key): str(value) for key, value in config.items()}


def lobby_player_to_engine(player: Player) -> EnginePlayer:
    avatar: dict[str, Any] | None = None
    if player.avatar_config is not None:
        avatar = player.avatar_config.config
    return EnginePlayer(
        id=str(player.id),
        name=player.name or "",
        sex=engine_sex_from_player(player.sex),
        game_age=player.game_age,
        game_relation_happiness=player.game_relation_happiness,
        avatar_config=_avatar_config_as_str_dict(avatar),
    )


def engine_player_to_dict(player: EnginePlayer) -> dict[str, Any]:
    avatar = dict(player.avatar_config) if player.avatar_config is not None else None
    return {
        "id": player.id,
        "name": player.name,
        "sex": player.sex.value,
        "game_age": player.game_age,
        "game_relation_happiness": player.game_relation_happiness,
        "simulation_age": player.simulation_age,
        "simulation_relation_happiness": player.simulation_relation_happiness,
        "avatar_config": avatar,
    }


def engine_player_from_dict(data: dict[str, Any]) -> EnginePlayer:
    avatar_raw = data.get("avatar_config")
    avatar = (
        _avatar_config_as_str_dict(avatar_raw) if isinstance(avatar_raw, dict) else None
    )
    return EnginePlayer(
        id=str(data["id"]),
        name=str(data["name"]),
        sex=PlayerSex(str(data["sex"])),
        game_age=int(data["game_age"]),
        game_relation_happiness=int(data["game_relation_happiness"]),
        simulation_age=int(data["simulation_age"]),
        simulation_relation_happiness=int(data["simulation_relation_happiness"]),
        avatar_config=avatar,
    )


def simulation_state_to_dict(state: SimulationState) -> dict[str, Any]:
    return {
        "partner_a": engine_player_to_dict(state.partner_a),
        "partner_b": engine_player_to_dict(state.partner_b),
        "finances": state.finances,
        "quality_of_life": state.quality_of_life,
        "children": state.children,
        "life_stage": state.life_stage.value,
        "relationship_status": state.relationship_status.value,
    }


def simulation_state_from_dict(data: dict[str, Any]) -> SimulationState:
    kwargs: dict[str, Any] = {
        "partner_a": engine_player_from_dict(data["partner_a"]),
        "partner_b": engine_player_from_dict(data["partner_b"]),
    }
    if "finances" in data:
        kwargs["finances"] = int(data["finances"])
    if "quality_of_life" in data:
        kwargs["quality_of_life"] = int(data["quality_of_life"])
    if "children" in data:
        kwargs["children"] = int(data["children"])
    if "life_stage" in data:
        kwargs["life_stage"] = LifeStage(str(data["life_stage"]))
    if "relationship_status" in data:
        kwargs["relationship_status"] = RelationshipStatus(
            str(data["relationship_status"]),
        )
    return SimulationState(**kwargs)


def public_simulation_state(state: SimulationState) -> dict[str, Any]:
    payload: dict[str, Any] = dict(state.to_dict())
    return payload


def _player_role_name(role: str) -> PlayerRoleName:
    if role not in ("partner_a", "partner_b"):
        raise AppError(
            "INVALID_PLAYER_ROLE",
            _("Invalid player role"),
            status_code=400,
        )
    return cast(PlayerRoleName, role)


def run_snapshot_from_orm(run: SimulationRun) -> RunSnapshot:
    answers = sorted(
        run.answers,
        key=lambda item: (item.sort_index is None, item.sort_index or 0),
    )
    timeline = sorted(
        run.timeline_entries,
        key=lambda item: (item.sort_index is None, item.sort_index or 0),
    )
    return RunSnapshot(
        run_id=str(run.id),
        player_role=_player_role_name(run.player_role),
        run_number=run.run_number,
        status=SessionStatus(run.status),
        rng_seed=run.rng_seed,
        events_played=run.events_played,
        events_played_ids=list(run.events_played_ids or []),
        timeline=[
            EngineTimelineEntry(
                title=entry.title,
                category=entry.category,
                age=entry.age,
                description=entry.description,
            )
            for entry in timeline
        ],
        answers=[
            RecordedAnswer(
                event_id=item.event_id,
                question_id=item.question_id,
                option_id=item.option_id,
                state_snapshot=None,
            )
            for item in answers
        ],
        event_variables=dict(run.event_variables or {}),
        current_event_id=run.current_event_id,
        end_reason=run.end_reason,
        max_events=run.max_events,
        state=simulation_state_from_dict(run.state_snapshot),
    )


def game_snapshot_from_db(game: Game, active_run: SimulationRun) -> GameSnapshot:
    partner_a_runs: list[RunSnapshot] = []
    for run in game.simulation_runs:
        if run.player_role != PlayerRole.PARTNER_A.value:
            continue
        if run.id == active_run.id:
            continue
        partner_a_runs.append(run_snapshot_from_orm(run))
    return GameSnapshot(
        game_id=str(game.id),
        mode=game.game_mode,
        active_run=run_snapshot_from_orm(active_run),
        partner_a_runs=partner_a_runs,
        config=GameConfig(max_events=active_run.max_events),
    )
