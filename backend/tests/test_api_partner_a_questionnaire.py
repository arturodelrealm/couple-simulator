from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.simulation_run import SimulationRun
from app.shared.enums import SimulationRunKind, SimulationRunStatus


def _create_ready_game(
    client: TestClient, match_name: str, avatar: dict[str, str]
) -> str:
    response = client.post(
        "/api/games",
        json={
            "match_name": match_name,
            "partner_a_name": "Alex",
            "partner_a_sex": "female",
            "avatar_config": avatar,
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def test_get_questionnaire_lists_a_eligible_events(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "q-get-eligible", valid_avatar_config)

    response = client.get(f"/api/games/{game_id}/partner-a/questionnaire")

    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert "errors" not in body
    payload = body["data"]
    event_ids = [item["event_id"] for item in payload["items"]]
    assert len(payload["items"]) == 21
    assert "work_party_crush" not in event_ids
    assert payload["progress"]["total"] == 21
    assert payload["progress"]["answered"] == 0
    assert payload["progress"]["skipped"] == 0
    assert payload["progress"]["complete"] is False
    assert all(item["status"] == "pending" for item in payload["items"])
    assert all(item["saved_answers"] == [] for item in payload["items"])
    going_bald = next(
        item for item in payload["items"] if item["event_id"] == "going_bald"
    )
    assert going_bald["presentation"]["title"].startswith("events.")
    assert going_bald["presentation"]["questions"]
    previews = going_bald["avatar_previews"]
    assert {
        (item["option_id"], item["player"], item["attribute"], item["value"])
        for item in previews
    } >= {
        ("let_nature", "partner_b", "topVariant", "noHair"),
        ("buzz_cut", "partner_b", "topVariant", "noHair"),
    }


def test_get_questionnaire_game_not_found(client: TestClient):
    response = client.get(f"/api/games/{uuid4()}/partner-a/questionnaire")

    assert response.status_code == 404
    assert response.json()["errors"][0]["code"] == "GAME_NOT_FOUND"


def test_get_questionnaire_game_not_ready(client: TestClient):
    create_response = client.post(
        "/api/games",
        json={"match_name": "q-get-not-ready", "partner_a_name": "Alex"},
    )
    game_id = create_response.json()["data"]["id"]

    response = client.get(f"/api/games/{game_id}/partner-a/questionnaire")

    assert response.status_code == 409
    assert response.json()["errors"][0]["code"] == "GAME_NOT_READY"


def _answers_url(game_id: str, event_id: str) -> str:
    return f"/api/games/{game_id}/partner-a/questionnaire/events/{event_id}/answers"


def _going_bald_answers() -> list[dict[str, str]]:
    return [{"question_id": "what_to_do", "option_id": "let_nature"}]


def _prep_run(db_session: Session, game_id: str) -> SimulationRun:
    db_session.expire_all()
    run = db_session.scalars(
        select(SimulationRun).where(
            SimulationRun.game_id == UUID(game_id),
            SimulationRun.run_kind == SimulationRunKind.QUESTIONNAIRE.value,
        )
    ).one()
    return run


def test_put_answers_stores_rows_and_marks_answered(
    client: TestClient,
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "q-put-ok", valid_avatar_config)

    response = client.put(
        _answers_url(game_id, "going_bald"),
        json={"answers": _going_bald_answers()},
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["item"]["status"] == "answered"
    assert body["item"]["saved_answers"] == _going_bald_answers()
    assert body["progress"]["answered"] == 1
    assert body["progress"]["complete"] is False

    listed = client.get(f"/api/games/{game_id}/partner-a/questionnaire")
    going_bald = next(
        item
        for item in listed.json()["data"]["items"]
        if item["event_id"] == "going_bald"
    )
    assert going_bald["status"] == "answered"
    assert going_bald["saved_answers"] == _going_bald_answers()

    prep = _prep_run(db_session, game_id)
    assert prep.events_played == 0
    assert prep.timeline_entries == []


def test_put_invalid_option_returns_409_and_leaves_snapshot(
    client: TestClient,
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "q-put-invalid", valid_avatar_config)
    client.get(f"/api/games/{game_id}/partner-a/questionnaire")
    prep = _prep_run(db_session, game_id)
    snapshot_before = dict(prep.state_snapshot)
    events_played_before = prep.events_played

    response = client.put(
        _answers_url(game_id, "going_bald"),
        json={"answers": [{"question_id": "what_to_do", "option_id": "nope"}]},
    )

    assert response.status_code == 409
    assert response.json()["errors"][0]["code"] == "INVALID_ANSWERS"
    prep = _prep_run(db_session, game_id)
    assert prep.state_snapshot == snapshot_before
    assert prep.events_played == events_played_before
    assert prep.answers == []


def test_put_missing_answers_returns_409(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "q-put-missing", valid_avatar_config)

    response = client.put(
        _answers_url(game_id, "how_well_do_you_know"),
        json={"answers": [{"question_id": "first_kiss", "option_id": "partner_a"}]},
    )

    assert response.status_code == 409
    assert response.json()["errors"][0]["code"] == "INVALID_ANSWERS"


def test_put_unknown_event_returns_404(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "q-put-unknown", valid_avatar_config)

    response = client.put(
        _answers_url(game_id, "work_party_crush"),
        json={"answers": [{"question_id": "q", "option_id": "o"}]},
    )

    assert response.status_code == 404
    assert response.json()["errors"][0]["code"] == "EVENT_NOT_FOUND"


def test_put_replaces_existing_option(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "q-put-edit", valid_avatar_config)
    first = client.put(
        _answers_url(game_id, "going_bald"),
        json={"answers": _going_bald_answers()},
    )
    assert first.status_code == 200

    second = client.put(
        _answers_url(game_id, "going_bald"),
        json={"answers": [{"question_id": "what_to_do", "option_id": "buzz_cut"}]},
    )

    assert second.status_code == 200
    assert second.json()["data"]["item"]["saved_answers"] == [
        {"question_id": "what_to_do", "option_id": "buzz_cut"}
    ]


def test_put_after_skip_clears_skip_and_stores_answers(
    client: TestClient,
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "q-put-unskip", valid_avatar_config)
    client.get(f"/api/games/{game_id}/partner-a/questionnaire")
    prep = _prep_run(db_session, game_id)
    prep.skipped_event_ids = ["going_bald"]
    db_session.commit()

    response = client.put(
        _answers_url(game_id, "going_bald"),
        json={"answers": _going_bald_answers()},
    )

    assert response.status_code == 200
    assert response.json()["data"]["item"]["status"] == "answered"
    prep = _prep_run(db_session, game_id)
    assert "going_bald" not in (prep.skipped_event_ids or [])
    assert [answer.option_id for answer in prep.answers] == ["let_nature"]


def _skip_url(game_id: str, event_id: str) -> str:
    return f"/api/games/{game_id}/partner-a/questionnaire/events/{event_id}/skip"


def _unskip_url(game_id: str, event_id: str) -> str:
    return f"/api/games/{game_id}/partner-a/questionnaire/events/{event_id}/unskip"


def test_skip_marks_event_and_clears_saved_answers(
    client: TestClient,
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "q-skip-ok", valid_avatar_config)

    response = client.post(_skip_url(game_id, "going_bald"))

    assert response.status_code == 200
    assert response.json()["data"]["item"]["status"] == "skipped"
    assert response.json()["data"]["item"]["saved_answers"] == []
    assert response.json()["data"]["progress"]["skipped"] == 1

    listed = client.get(f"/api/games/{game_id}/partner-a/questionnaire")
    going_bald = next(
        item
        for item in listed.json()["data"]["items"]
        if item["event_id"] == "going_bald"
    )
    assert going_bald["status"] == "skipped"
    assert going_bald["saved_answers"] == []
    prep = _prep_run(db_session, game_id)
    assert "going_bald" in (prep.skipped_event_ids or [])
    assert prep.events_played == 0


def test_skip_after_answers_deletes_rows(
    client: TestClient,
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "q-skip-after-answer", valid_avatar_config)
    put = client.put(
        _answers_url(game_id, "going_bald"),
        json={"answers": _going_bald_answers()},
    )
    assert put.status_code == 200
    prep = _prep_run(db_session, game_id)
    snapshot_before = dict(prep.state_snapshot)

    response = client.post(_skip_url(game_id, "going_bald"))

    assert response.status_code == 200
    assert response.json()["data"]["item"]["status"] == "skipped"
    prep = _prep_run(db_session, game_id)
    assert prep.answers == []
    assert prep.state_snapshot == snapshot_before


def test_skip_is_idempotent(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "q-skip-again", valid_avatar_config)
    first = client.post(_skip_url(game_id, "going_bald"))
    second = client.post(_skip_url(game_id, "going_bald"))

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["data"]["item"]["status"] == "skipped"
    assert second.json()["data"]["progress"]["skipped"] == 1


def test_unskip_returns_pending(
    client: TestClient,
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "q-unskip", valid_avatar_config)
    client.post(_skip_url(game_id, "going_bald"))

    response = client.post(_unskip_url(game_id, "going_bald"))

    assert response.status_code == 200
    assert response.json()["data"]["item"]["status"] == "pending"
    assert response.json()["data"]["progress"]["skipped"] == 0
    prep = _prep_run(db_session, game_id)
    assert "going_bald" not in (prep.skipped_event_ids or [])
    assert prep.status == SimulationRunStatus.ACTIVE.value


def test_skip_unknown_event_returns_404(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "q-skip-unknown", valid_avatar_config)

    response = client.post(_skip_url(game_id, "work_party_crush"))

    assert response.status_code == 404
    assert response.json()["errors"][0]["code"] == "EVENT_NOT_FOUND"


def test_complete_questionnaire_then_unskip_reactivates(
    client: TestClient,
    db_session: Session,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "q-complete-unskip", valid_avatar_config)
    listed = client.get(f"/api/games/{game_id}/partner-a/questionnaire")
    for item in listed.json()["data"]["items"]:
        skip = client.post(_skip_url(game_id, item["event_id"]))
        assert skip.status_code == 200

    finished = client.get(f"/api/games/{game_id}/partner-a/questionnaire")
    assert finished.json()["data"]["progress"]["complete"] is True
    prep = _prep_run(db_session, game_id)
    assert prep.status == SimulationRunStatus.FINISHED.value
    assert prep.end_reason == "questionnaire_complete"

    unskip = client.post(_unskip_url(game_id, "going_bald"))
    assert unskip.status_code == 200
    assert unskip.json()["data"]["progress"]["complete"] is False
    prep = _prep_run(db_session, game_id)
    assert prep.status == SimulationRunStatus.ACTIVE.value
    assert prep.end_reason is None


def test_partner_b_can_start_with_incomplete_questionnaire(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "q-b-anytime", valid_avatar_config)
    client.post(_skip_url(game_id, "going_bald"))
    patched = client.patch(
        f"/api/games/{game_id}",
        json={
            "partner_b_name": "Blake",
            "partner_b_sex": "male",
            "partner_b_avatar_config": valid_avatar_config,
        },
    )
    assert patched.status_code == 200

    response = client.post(
        f"/api/games/{game_id}/simulation/runs",
        json={"player_role": "partner_b", "seed": 3},
    )
    assert response.status_code == 201
    assert response.json()["data"]["player_role"] == "partner_b"
