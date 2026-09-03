from uuid import uuid4

from fastapi.testclient import TestClient


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


def test_post_then_get_run_includes_timeline_and_answers(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "api-sim-get", valid_avatar_config)

    post_response = client.post(
        f"/api/games/{game_id}/simulation/runs",
        json={"player_role": "partner_a", "seed": 21},
    )
    assert post_response.status_code == 201
    created = post_response.json()["data"]
    run_id = created["run_id"]
    assert created["status"] == "ACTIVE"
    assert created["events_played"] == 0
    assert "state" in created
    assert "age" in created["state"]
    assert "career" not in created["state"]
    assert "adventures" not in created["state"]
    assert "current_event" not in created
    assert "event" not in created

    get_response = client.get(f"/api/games/{game_id}/simulation/runs/{run_id}")
    assert get_response.status_code == 200
    body = get_response.json()["data"]
    assert body["run_id"] == run_id
    assert body["timeline"] == []
    assert body["answers"] == []
    assert body["rng_seed"] == 21

    lobby = client.get(f"/api/games/{game_id}")
    assert lobby.status_code == 200
    assert lobby.json()["data"]["status"] == "PLAYER_A_READY"
    assert "simulation" not in lobby.json()["data"]
    assert lobby.json()["data"]["partner_a"]["name"] == "Alex"


def test_post_without_seed_persists_numeric_seed(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "api-sim-random-seed", valid_avatar_config)

    post_response = client.post(
        f"/api/games/{game_id}/simulation/runs",
        json={"player_role": "partner_a"},
    )
    assert post_response.status_code == 201
    run_id = post_response.json()["data"]["run_id"]

    get_response = client.get(f"/api/games/{game_id}/simulation/runs/{run_id}")
    seed = get_response.json()["data"]["rng_seed"]
    assert isinstance(seed, int)


def test_post_created_game_returns_409(
    client: TestClient,
):
    create_response = client.post(
        "/api/games",
        json={"match_name": "api-sim-not-ready", "partner_a_name": "Alex"},
    )
    game_id = create_response.json()["data"]["id"]

    response = client.post(
        f"/api/games/{game_id}/simulation/runs",
        json={"player_role": "partner_a"},
    )

    assert response.status_code == 409
    assert response.json()["errors"][0]["code"] == "GAME_NOT_READY"


def test_list_runs_returns_both_and_status_filter(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "api-sim-list", valid_avatar_config)

    first = client.post(
        f"/api/games/{game_id}/simulation/runs",
        json={"player_role": "partner_a", "seed": 1},
    )
    second = client.post(
        f"/api/games/{game_id}/simulation/runs",
        json={"player_role": "partner_a", "seed": 2},
    )
    assert first.status_code == 201
    assert second.status_code == 201

    listed = client.get(f"/api/games/{game_id}/simulation/runs")
    assert listed.status_code == 200
    payload = listed.json()["data"]
    assert "items" in payload
    assert "pagination" in payload
    assert payload["pagination"]["total"] == 2
    assert {item["run_id"] for item in payload["items"]} == {
        first.json()["data"]["run_id"],
        second.json()["data"]["run_id"],
    }
    for item in payload["items"]:
        assert "run_number" in item
        assert "created_at" in item
        assert item["player_role"] == "partner_a"

    active = client.get(
        f"/api/games/{game_id}/simulation/runs",
        params={"status": "ACTIVE"},
    )
    assert active.status_code == 200
    assert active.json()["data"]["pagination"]["total"] == 2


def test_post_partner_b_run_requires_complete_lobby_b(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "api-sim-partner-b-gate", valid_avatar_config)

    incomplete = client.post(
        f"/api/games/{game_id}/simulation/runs",
        json={"player_role": "partner_b", "seed": 3},
    )
    assert incomplete.status_code == 409
    assert incomplete.json()["errors"][0]["code"] == "PARTNER_B_NOT_READY"

    patched = client.patch(
        f"/api/games/{game_id}",
        json={
            "partner_b_name": "Blake",
            "partner_b_sex": "male",
            "partner_b_avatar_config": valid_avatar_config,
        },
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["status"] == "PLAYER_A_READY"

    response = client.post(
        f"/api/games/{game_id}/simulation/runs",
        json={"player_role": "partner_b", "seed": 3},
    )
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["player_role"] == "partner_b"
    assert body["status"] == "ACTIVE"

    lobby = client.get(f"/api/games/{game_id}")
    assert lobby.status_code == 200
    assert lobby.json()["data"]["status"] == "PLAYER_B_PLAYING"

    a_after_b = client.post(
        f"/api/games/{game_id}/simulation/runs",
        json={"player_role": "partner_a", "seed": 4},
    )
    assert a_after_b.status_code == 201

    patch_a = client.patch(
        f"/api/games/{game_id}",
        json={"partner_a_name": "Jordan"},
    )
    assert patch_a.status_code == 200
    assert patch_a.json()["data"]["status"] == "PLAYER_B_PLAYING"
    assert patch_a.json()["data"]["partner_a"]["name"] == "Jordan"

    listed = client.get(
        f"/api/games/{game_id}/simulation/runs",
        params={"player_role": "partner_b"},
    )
    assert listed.status_code == 200
    payload = listed.json()["data"]
    assert payload["pagination"]["total"] == 1
    assert payload["items"][0]["run_id"] == body["run_id"]
    assert payload["items"][0]["player_role"] == "partner_b"

    invalid = client.get(
        f"/api/games/{game_id}/simulation/runs",
        params={"player_role": "npc"},
    )
    assert invalid.status_code == 400
    assert invalid.json()["errors"][0]["code"] == "INVALID_PLAYER_ROLE"


def test_get_current_event_after_start(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "api-sim-current", valid_avatar_config)
    started = client.post(
        f"/api/games/{game_id}/simulation/runs",
        json={"player_role": "partner_a", "seed": 15},
    )
    run_id = started.json()["data"]["run_id"]

    current = client.get(
        f"/api/games/{game_id}/simulation/runs/{run_id}/events/current",
    )
    assert current.status_code == 200
    event = current.json()["data"]["event"]
    assert event["event_id"]
    assert event["questions"]
    assert "options" in event["questions"][0]

    run = client.get(f"/api/games/{game_id}/simulation/runs/{run_id}")
    assert run.json()["data"]["current_event_id"] == event["event_id"]
    events_played = run.json()["data"]["events_played"]

    again = client.get(
        f"/api/games/{game_id}/simulation/runs/{run_id}/events/current",
    )
    assert again.json()["data"]["event"]["event_id"] == event["event_id"]
    run_again = client.get(f"/api/games/{game_id}/simulation/runs/{run_id}")
    assert run_again.json()["data"]["events_played"] == events_played


def test_get_current_event_unknown_run_is_404(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "api-sim-missing-run", valid_avatar_config)
    response = client.get(
        f"/api/games/{game_id}/simulation/runs/{uuid4()}/events/current",
    )
    assert response.status_code == 404
    assert response.json()["errors"][0]["code"] == "RUN_NOT_FOUND"


def _continue_answers(event: dict) -> list[dict[str, str]]:
    answers: list[dict[str, str]] = []
    for question in event["questions"]:
        option_id = question["options"][0]["id"]
        if event["event_id"] == "burnout":
            option_id = next(
                option["id"]
                for option in question["options"]
                if option["id"] == "push_through"
            )
        answers.append(
            {
                "question_id": question["id"],
                "option_id": option_id,
            }
        )
    return answers


def test_submit_answers_updates_run_and_advances_current_event(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "api-sim-submit", valid_avatar_config)
    started = client.post(
        f"/api/games/{game_id}/simulation/runs",
        json={"player_role": "partner_a", "seed": 15, "max_events": 5},
    )
    run_id = started.json()["data"]["run_id"]
    lobby_before = client.get(f"/api/games/{game_id}")
    lobby_age = lobby_before.json()["data"]["partner_a"]["game_age"]

    current = client.get(
        f"/api/games/{game_id}/simulation/runs/{run_id}/events/current",
    )
    event = current.json()["data"]["event"]
    event_id = event["event_id"]

    submit = client.post(
        f"/api/games/{game_id}/simulation/runs/{run_id}/events/{event_id}/answers",
        json={"answers": _continue_answers(event)},
    )
    assert submit.status_code == 200
    body = submit.json()["data"]
    assert body["run_id"] == run_id
    assert body["events_played"] == 1
    assert "client_actions" in body
    assert isinstance(body["client_actions"], list)
    for action in body["client_actions"]:
        assert "type" in action
        assert "args" in action
    assert "state" in body
    assert "career" not in body["state"]
    assert "adventures" not in body["state"]
    assert "game_finished" in body
    assert "event" not in body

    run = client.get(f"/api/games/{game_id}/simulation/runs/{run_id}")
    run_data = run.json()["data"]
    assert run_data["current_event_id"] is None
    assert run_data["answers"]
    assert all(item["event_id"] == event_id for item in run_data["answers"])

    lobby_after = client.get(f"/api/games/{game_id}")
    assert lobby_after.json()["data"]["partner_a"]["game_age"] == lobby_age

    next_current = client.get(
        f"/api/games/{game_id}/simulation/runs/{run_id}/events/current",
    )
    if body["game_finished"] or run_data["status"] == "FINISHED":
        assert next_current.status_code == 409
        assert next_current.json()["errors"][0]["code"] in {
            "RUN_FINISHED",
            "NO_ELIGIBLE_EVENTS",
        }
    else:
        assert next_current.status_code == 200
        assert next_current.json()["data"]["event"]["event_id"] != event_id


def test_submit_answers_unknown_run_is_404(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "api-sim-submit-missing", valid_avatar_config)
    response = client.post(
        f"/api/games/{game_id}/simulation/runs/{uuid4()}/events/any/answers",
        json={"answers": [{"question_id": "q", "option_id": "o"}]},
    )
    assert response.status_code == 404
    assert response.json()["errors"][0]["code"] == "RUN_NOT_FOUND"


def _complete_partner_b(
    client: TestClient,
    game_id: str,
    avatar: dict[str, str],
) -> None:
    patched = client.patch(
        f"/api/games/{game_id}",
        json={
            "partner_b_name": "Blake",
            "partner_b_sex": "male",
            "partner_b_avatar_config": avatar,
        },
    )
    assert patched.status_code == 200
    partner_b = patched.json()["data"]["partner_b"]
    assert partner_b["name"] == "Blake"


def _compatibility_actions(client_actions: list[dict]) -> list[dict]:
    return [
        action
        for action in client_actions
        if action["type"] == "modify_stat"
        and action["args"].get("variable") == "compatibility"
    ]


def _get_current_event(client: TestClient, game_id: str, run_id: str) -> dict:
    current = client.get(
        f"/api/games/{game_id}/simulation/runs/{run_id}/events/current",
    )
    assert current.status_code == 200
    payload = current.json()["data"]
    assert "partner_answers" not in payload
    assert "partner_answers" not in payload["event"]
    return payload["event"]


def _submit_event(
    client: TestClient,
    game_id: str,
    run_id: str,
    event: dict,
    answers: list[dict[str, str]],
) -> dict:
    submit = client.post(
        f"/api/games/{game_id}/simulation/runs/{run_id}/events/"
        f"{event['event_id']}/answers",
        json={"answers": answers},
    )
    assert submit.status_code == 200
    return submit.json()["data"]


def _answers_by_event(run_answers: list[dict]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for item in run_answers:
        grouped.setdefault(item["event_id"], []).append(
            {
                "question_id": item["question_id"],
                "option_id": item["option_id"],
            }
        )
    return grouped


def test_http_a_then_b_applies_couple_when_bank_covers_event(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "api-sim-a-then-b", valid_avatar_config)
    happiness = client.patch(
        f"/api/games/{game_id}",
        json={"partner_a_game_relation_happiness": 70},
    )
    assert happiness.status_code == 200

    started_a = client.post(
        f"/api/games/{game_id}/simulation/runs",
        json={"player_role": "partner_a", "seed": 11, "max_events": 1},
    )
    assert started_a.status_code == 201
    a_run_id = started_a.json()["data"]["run_id"]
    a_event = _get_current_event(client, game_id, a_run_id)
    a_answers = _continue_answers(a_event)
    a_submit = _submit_event(client, game_id, a_run_id, a_event, a_answers)
    assert a_submit["events_played"] == 1
    assert _compatibility_actions(a_submit["client_actions"]) == []

    a_detail = client.get(f"/api/games/{game_id}/simulation/runs/{a_run_id}")
    assert a_detail.status_code == 200
    bank = _answers_by_event(a_detail.json()["data"]["answers"])
    assert a_event["event_id"] in bank

    _complete_partner_b(client, game_id, valid_avatar_config)

    started_b = client.post(
        f"/api/games/{game_id}/simulation/runs",
        json={"player_role": "partner_b", "seed": 11, "max_events": 5},
    )
    assert started_b.status_code == 201
    b_run_id = started_b.json()["data"]["run_id"]
    assert started_b.json()["data"]["player_role"] == "partner_b"

    lobby = client.get(f"/api/games/{game_id}")
    assert lobby.status_code == 200
    assert lobby.json()["data"]["status"] == "PLAYER_B_PLAYING"
    assert lobby.json()["data"]["partner_b"]["name"] == "Blake"

    listed_a = client.get(
        f"/api/games/{game_id}/simulation/runs",
        params={"player_role": "partner_a"},
    )
    listed_b = client.get(
        f"/api/games/{game_id}/simulation/runs",
        params={"player_role": "partner_b"},
    )
    assert listed_a.json()["data"]["pagination"]["total"] == 1
    assert listed_a.json()["data"]["items"][0]["run_id"] == a_run_id
    assert listed_b.json()["data"]["pagination"]["total"] == 1
    assert listed_b.json()["data"]["items"][0]["run_id"] == b_run_id

    couple_hit = False
    for _ in range(5):
        b_event = _get_current_event(client, game_id, b_run_id)
        answers = bank.get(b_event["event_id"], _continue_answers(b_event))
        result = _submit_event(client, game_id, b_run_id, b_event, answers)
        if b_event["event_id"] in bank:
            match_actions = _compatibility_actions(result["client_actions"])
            assert match_actions
            assert any(action["args"].get("delta") == 5 for action in match_actions)
            couple_hit = True
            break
        assert _compatibility_actions(result["client_actions"]) == []
        if result["game_finished"] or result["status"] == "FINISHED":
            break

    assert couple_hit, "expected a bank-covered event on the Partner B run"


def test_http_partner_b_start_with_zero_a_runs_is_solo_like(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    game_id = _create_ready_game(client, "api-sim-b-empty-bank", valid_avatar_config)
    _complete_partner_b(client, game_id, valid_avatar_config)

    listed_a = client.get(
        f"/api/games/{game_id}/simulation/runs",
        params={"player_role": "partner_a"},
    )
    assert listed_a.json()["data"]["pagination"]["total"] == 0

    started_b = client.post(
        f"/api/games/{game_id}/simulation/runs",
        json={"player_role": "partner_b", "seed": 11, "max_events": 5},
    )
    assert started_b.status_code == 201
    b_run_id = started_b.json()["data"]["run_id"]
    compatibility_before = started_b.json()["data"]["state"]["compatibility"]

    lobby = client.get(f"/api/games/{game_id}")
    assert lobby.json()["data"]["status"] == "PLAYER_B_PLAYING"

    event = _get_current_event(client, game_id, b_run_id)
    result = _submit_event(
        client,
        game_id,
        b_run_id,
        event,
        _continue_answers(event),
    )
    assert _compatibility_actions(result["client_actions"]) == []
    assert result["state"]["compatibility"] == compatibility_before
    assert result["events_played"] == 1

    listed_b = client.get(
        f"/api/games/{game_id}/simulation/runs",
        params={"player_role": "partner_b"},
    )
    assert listed_b.json()["data"]["pagination"]["total"] == 1
    assert listed_b.json()["data"]["items"][0]["run_id"] == b_run_id

