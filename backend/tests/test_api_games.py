from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"data": {"status": "ok"}}


def test_create_and_get_game(client: TestClient):
    create_response = client.post(
        "/api/games",
        json={"partner_a_name": "Alex"},
    )

    assert create_response.status_code == 201
    created = create_response.json()["data"]
    assert created["status"] == "CREATED"
    assert created["partner_a"]["name"] == "Alex"

    get_response = client.get(f"/api/games/{created['id']}")

    assert get_response.status_code == 200
    assert get_response.json()["data"] == created


def test_patch_game_updates_avatar_and_status(
    client: TestClient,
    valid_avatar_config: dict[str, str],
):
    create_response = client.post(
        "/api/games",
        json={"partner_a_name": "Alex"},
    )
    game_id = create_response.json()["data"]["id"]

    patch_response = client.patch(
        f"/api/games/{game_id}",
        json={"avatar_config": valid_avatar_config},
    )

    assert patch_response.status_code == 200
    body = patch_response.json()["data"]
    assert body["status"] == "PLAYER_A_READY"
    assert body["partner_a"]["avatar_config"] == valid_avatar_config


def test_get_game_not_found_returns_structured_error(client: TestClient):
    response = client.get("/api/games/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    errors = response.json()["errors"]
    assert errors[0]["code"] == "GAME_NOT_FOUND"
