from fastapi.testclient import TestClient

from app.config import settings


def test_health_check(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"data": {"status": "ok"}}


def test_create_and_get_game(client: TestClient):
    create_response = client.post(
        "/api/games",
        json={
            "match_name": "boda-ana-luis",
            "game_mode": "couple",
            "partner_a_name": "Alex",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()["data"]
    assert created["match_name"] == "boda-ana-luis"
    assert created["game_mode"] == "couple"
    assert created["status"] == "CREATED"
    assert created["partner_a"]["name"] == "Alex"
    assert created["partner_a"]["game_age"] == 22
    assert created["partner_a"]["game_relation_happiness"] == 100
    assert created["partner_b"] is None

    get_response = client.get(f"/api/games/{created['id']}")

    assert get_response.status_code == 200
    assert get_response.json()["data"] == created


def test_create_game_with_complete_setup_is_player_a_ready(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    response = client.post(
        "/api/games",
        json={
            "match_name": "complete-setup",
            "partner_a_name": "Alex",
            "partner_a_sex": "female",
            "avatar_config": valid_avatar_config,
        },
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["status"] == "PLAYER_A_READY"
    assert body["partner_a"]["sex"] == "female"
    assert body["partner_a"]["avatar_config"] == valid_avatar_config


def test_create_game_duplicate_match_name_is_case_insensitive(client: TestClient):
    first = client.post(
        "/api/games",
        json={"match_name": "Boda"},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/games",
        json={"match_name": "boda"},
    )

    assert second.status_code == 409
    errors = second.json()["errors"]
    assert errors[0]["code"] == "MATCH_NAME_TAKEN"
    assert errors[0]["message"] == "Match name is already taken"


def test_create_game_duplicate_match_name_returns_spanish_message(
    client: TestClient,
):
    client.post("/api/games", json={"match_name": "spanish-name"})

    response = client.post(
        "/api/games",
        json={"match_name": "spanish-name"},
        headers={"Accept-Language": "es"},
    )

    assert response.status_code == 409
    message = response.json()["errors"][0]["message"]
    assert message == "Ese nombre de partida ya está en uso. Elige otro."


def test_create_game_invalid_match_name_returns_422(client: TestClient):
    response = client.post(
        "/api/games",
        json={"match_name": "ab"},
    )

    assert response.status_code == 422


def test_get_game_by_match_name(client: TestClient):
    create_response = client.post(
        "/api/games",
        json={"match_name": "find-me-game"},
    )
    created = create_response.json()["data"]

    get_response = client.get("/api/games/by-match-name/find-me-game")

    assert get_response.status_code == 200
    assert get_response.json()["data"]["id"] == created["id"]
    assert get_response.json()["data"]["match_name"] == "find-me-game"
    assert get_response.json()["data"]["partner_b"] is None


def test_get_game_by_match_name_case_insensitive(client: TestClient):
    client.post(
        "/api/games",
        json={"match_name": "MixedCase"},
    )

    get_response = client.get("/api/games/by-match-name/mixedcase")

    assert get_response.status_code == 200
    assert get_response.json()["data"]["match_name"] == "mixedcase"


def test_get_game_by_match_name_not_found(client: TestClient):
    response = client.get("/api/games/by-match-name/does-not-exist")

    assert response.status_code == 404
    errors = response.json()["errors"]
    assert errors[0]["code"] == "GAME_NOT_FOUND"


def test_patch_game_updates_avatar_sex_and_status(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    create_response = client.post(
        "/api/games",
        json={
            "match_name": "patch-test",
            "partner_a_name": "Alex",
        },
    )
    game_id = create_response.json()["data"]["id"]

    patch_response = client.patch(
        f"/api/games/{game_id}",
        json={
            "avatar_config": valid_avatar_config,
            "partner_a_sex": "male",
        },
    )

    assert patch_response.status_code == 200
    body = patch_response.json()["data"]
    assert body["status"] == "PLAYER_A_READY"
    assert body["partner_a"]["avatar_config"] == valid_avatar_config
    assert body["partner_a"]["sex"] == "male"


def test_patch_game_without_sex_stays_created(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    create_response = client.post(
        "/api/games",
        json={
            "match_name": "no-sex-yet",
            "partner_a_name": "Alex",
        },
    )
    game_id = create_response.json()["data"]["id"]

    patch_response = client.patch(
        f"/api/games/{game_id}",
        json={"avatar_config": valid_avatar_config},
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["data"]["status"] == "CREATED"


def test_get_game_not_found_returns_structured_error(client: TestClient):
    response = client.get("/api/games/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    errors = response.json()["errors"]
    assert errors[0]["code"] == "GAME_NOT_FOUND"


def test_get_game_invite(client: TestClient):
    create_response = client.post(
        "/api/games",
        json={"match_name": "invite-me"},
    )
    game_id = create_response.json()["data"]["id"]

    response = client.get(f"/api/games/{game_id}/invite")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["game_id"] == game_id
    assert body["match_name"] == "invite-me"
    assert body["invite_path"] == "/games/join/invite-me"
    if settings.frontend_public_url:
        expected_url = (
            f"{settings.frontend_public_url.rstrip('/')}/games/join/invite-me"
        )
        assert body["invite_url"] == expected_url
    else:
        assert body["invite_url"] is None


def test_get_game_invite_not_found(client: TestClient):
    response = client.get(
        "/api/games/00000000-0000-0000-0000-000000000000/invite",
    )

    assert response.status_code == 404
    assert response.json()["errors"][0]["code"] == "GAME_NOT_FOUND"


def test_patch_game_updates_game_stats_without_setup_fields(client: TestClient):
    create_response = client.post(
        "/api/games",
        json={"match_name": "patch-stats-only"},
    )
    game_id = create_response.json()["data"]["id"]
    assert create_response.json()["data"]["partner_a"]["game_age"] == 22

    patch_response = client.patch(
        f"/api/games/{game_id}",
        json={
            "partner_a_game_age": 28,
            "partner_a_game_relation_happiness": 55,
        },
    )

    assert patch_response.status_code == 200
    body = patch_response.json()["data"]
    assert body["status"] == "CREATED"
    assert body["partner_a"]["game_age"] == 28
    assert body["partner_a"]["game_relation_happiness"] == 55


def test_patch_game_rejects_game_age_below_18(client: TestClient):
    create_response = client.post(
        "/api/games",
        json={"match_name": "patch-age-invalid"},
    )
    game_id = create_response.json()["data"]["id"]

    patch_response = client.patch(
        f"/api/games/{game_id}",
        json={"partner_a_game_age": 17},
    )

    assert patch_response.status_code == 400
    error = patch_response.json()["errors"][0]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["field"] == "body.partner_a_game_age"


def test_create_game_with_game_stats(client: TestClient):
    response = client.post(
        "/api/games",
        json={
            "match_name": "create-with-stats",
            "partner_a_game_age": 35,
            "partner_a_game_relation_happiness": 70,
        },
    )

    assert response.status_code == 201
    partner_a = response.json()["data"]["partner_a"]
    assert partner_a["game_age"] == 35
    assert partner_a["game_relation_happiness"] == 70


def test_patch_partner_b_creates_and_updates_same_row(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    create_response = client.post(
        "/api/games",
        json={"match_name": "partner-b-lobby"},
    )
    game_id = create_response.json()["data"]["id"]
    assert create_response.json()["data"]["partner_b"] is None

    first_patch = client.patch(
        f"/api/games/{game_id}",
        json={
            "partner_b_name": "Blake",
            "partner_b_sex": "male",
            "partner_b_avatar_config": valid_avatar_config,
            "partner_b_game_age": 26,
            "partner_b_game_relation_happiness": 80,
        },
    )
    assert first_patch.status_code == 200
    first_body = first_patch.json()["data"]
    assert first_body["partner_b"]["name"] == "Blake"
    assert first_body["partner_b"]["sex"] == "male"
    assert first_body["partner_b"]["avatar_config"] == valid_avatar_config
    assert first_body["partner_b"]["game_age"] == 26
    assert first_body["partner_b"]["game_relation_happiness"] == 80
    assert first_body["partner_a"]["name"] is None

    second_patch = client.patch(
        f"/api/games/{game_id}",
        json={"partner_b_name": "Riley"},
    )
    assert second_patch.status_code == 200
    second_body = second_patch.json()["data"]
    assert second_body["partner_b"]["name"] == "Riley"
    assert second_body["partner_b"]["sex"] == "male"
    assert second_body["partner_b"]["game_age"] == 26

    by_name = client.get("/api/games/by-match-name/partner-b-lobby")
    assert by_name.status_code == 200
    assert by_name.json()["data"]["partner_b"]["name"] == "Riley"


def test_patch_mixes_partner_a_and_partner_b_fields(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    create_response = client.post(
        "/api/games",
        json={"match_name": "mix-partners", "partner_a_name": "Alex"},
    )
    game_id = create_response.json()["data"]["id"]

    patch_response = client.patch(
        f"/api/games/{game_id}",
        json={
            "partner_a_sex": "female",
            "avatar_config": valid_avatar_config,
            "partner_b_name": "Blake",
        },
    )

    assert patch_response.status_code == 200
    body = patch_response.json()["data"]
    assert body["status"] == "PLAYER_A_READY"
    assert body["partner_a"]["name"] == "Alex"
    assert body["partner_a"]["sex"] == "female"
    assert body["partner_b"]["name"] == "Blake"
    assert body["partner_b"]["sex"] is None
    assert body["partner_b"]["game_age"] == 22
    assert body["partner_b"]["game_relation_happiness"] == 100


def test_patch_game_empty_body_still_400(client: TestClient):
    create_response = client.post(
        "/api/games",
        json={"match_name": "empty-patch-api"},
    )
    game_id = create_response.json()["data"]["id"]

    patch_response = client.patch(f"/api/games/{game_id}", json={})

    assert patch_response.status_code == 400
    assert patch_response.json()["errors"][0]["code"] == "BAD_REQUEST"
