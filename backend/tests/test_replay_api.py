from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def signup(prefix: str) -> str:
    suffix = uuid4().hex
    response = client.post(
        "/api/auth/signup",
        json={
            "email": f"{prefix}-{suffix}@example.com",
            "username": f"{prefix}_{suffix}",
            "password": "Password123!",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def match_payload(replay_filename: str | None = None) -> dict:
    return {
        "player_character": "Sol Badguy",
        "opponent_character": "Ky Kiske",
        "result": "win",
        "played_on": date(2026, 7, 1).isoformat(),
        "rank_floor": "Gold",
        "duration_seconds": 180,
        "rounds_won": 2,
        "rounds_lost": 1,
        "first_to": 2,
        "notes": "Replay API test match.",
        "mistake_tags": [],
        "strength_tags": [],
        "reason_for_loss": None,
        "practice_next": None,
        "replay_filename": replay_filename,
    }


def create_match(token: str, replay_filename: str | None = None) -> dict:
    response = client.post("/api/matches", json=match_payload(replay_filename), headers=auth_headers(token))
    assert response.status_code == 201
    return response.json()


def create_replay(token: str, match_id: int, source_type: str = "replay_file", original_filename: str | None = "set-vs-ky.rep") -> dict:
    response = client.post(
        f"/api/matches/{match_id}/replays",
        json={"source_type": source_type, "original_filename": original_filename},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    return response.json()


def test_replay_endpoints_require_authentication():
    token = signup("replay_auth")
    match = create_match(token)
    replay = create_replay(token, match["id"])

    assert client.get(f"/api/matches/{match['id']}/replays").status_code == 401
    assert client.post(f"/api/matches/{match['id']}/replays", json={"source_type": "video"}).status_code == 401
    assert client.get(f"/api/matches/{match['id']}/replays/{replay['id']}").status_code == 401
    assert client.patch(f"/api/matches/{match['id']}/replays/{replay['id']}", json={"source_type": "video"}).status_code == 401
    assert client.delete(f"/api/matches/{match['id']}/replays/{replay['id']}").status_code == 401


def test_create_replay_on_owned_match_sets_match_id_and_trims_filename():
    token = signup("replay_create")
    match = create_match(token)

    response = client.post(
        f"/api/matches/{match['id']}/replays",
        json={"source_type": "replay_file", "original_filename": " set-vs-ky.rep "},
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["match_id"] == match["id"]
    assert body["source_type"] == "replay_file"
    assert body["original_filename"] == "set-vs-ky.rep"
    assert "created_at" in body
    assert "updated_at" in body


def test_supported_source_types_and_nullable_filename_work():
    token = signup("replay_sources")
    match = create_match(token)

    for source_type in ["replay_file", "video", "external_reference"]:
        replay = create_replay(token, match["id"], source_type=source_type, original_filename=None)
        assert replay["source_type"] == source_type
        assert replay["original_filename"] is None


def test_invalid_source_type_and_long_filename_are_rejected():
    token = signup("replay_invalid")
    match = create_match(token)

    invalid_source = client.post(
        f"/api/matches/{match['id']}/replays",
        json={"source_type": "screenshot", "original_filename": "screen.png"},
        headers=auth_headers(token),
    )
    long_filename = client.post(
        f"/api/matches/{match['id']}/replays",
        json={"source_type": "video", "original_filename": "x" * 256},
        headers=auth_headers(token),
    )

    assert invalid_source.status_code == 422
    assert long_filename.status_code == 422


def test_collection_read_zero_one_multiple_and_ordering():
    token = signup("replay_collection")
    match = create_match(token)

    empty = client.get(f"/api/matches/{match['id']}/replays", headers=auth_headers(token))
    assert empty.status_code == 200
    assert empty.json() == []

    first = create_replay(token, match["id"], source_type="replay_file", original_filename="first.rep")
    second = create_replay(token, match["id"], source_type="video", original_filename="second.mp4")

    response = client.get(f"/api/matches/{match['id']}/replays", headers=auth_headers(token))

    assert response.status_code == 200
    body = response.json()
    assert [replay["id"] for replay in body] == [first["id"], second["id"]]
    assert [replay["match_id"] for replay in body] == [match["id"], match["id"]]


def test_owner_can_read_replay_and_missing_or_wrong_match_returns_404():
    token = signup("replay_read")
    match_a = create_match(token)
    match_b = create_match(token)
    replay = create_replay(token, match_a["id"])

    owned = client.get(f"/api/matches/{match_a['id']}/replays/{replay['id']}", headers=auth_headers(token))
    nonexistent = client.get(f"/api/matches/{match_a['id']}/replays/99999999", headers=auth_headers(token))
    wrong_match = client.get(f"/api/matches/{match_b['id']}/replays/{replay['id']}", headers=auth_headers(token))

    assert owned.status_code == 200
    assert owned.json()["id"] == replay["id"]
    assert nonexistent.status_code == 404
    assert wrong_match.status_code == 404


def test_owner_can_patch_replay_metadata_partially_without_moving_match():
    token = signup("replay_patch")
    match = create_match(token)
    replay = create_replay(token, match["id"], source_type="replay_file", original_filename="before.rep")

    source_update = client.patch(
        f"/api/matches/{match['id']}/replays/{replay['id']}",
        json={"source_type": "video"},
        headers=auth_headers(token),
    )
    filename_update = client.patch(
        f"/api/matches/{match['id']}/replays/{replay['id']}",
        json={"original_filename": " after.mp4 "},
        headers=auth_headers(token),
    )
    attempted_move = client.patch(
        f"/api/matches/{match['id']}/replays/{replay['id']}",
        json={"match_id": match["id"] + 999, "source_type": "external_reference"},
        headers=auth_headers(token),
    )
    after_attempted_move = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token))

    assert source_update.status_code == 200
    assert source_update.json()["source_type"] == "video"
    assert source_update.json()["original_filename"] == "before.rep"
    assert filename_update.status_code == 200
    assert filename_update.json()["source_type"] == "video"
    assert filename_update.json()["original_filename"] == "after.mp4"
    assert attempted_move.status_code == 422
    assert after_attempted_move.status_code == 200
    assert after_attempted_move.json()["match_id"] == match["id"]
    assert after_attempted_move.json()["source_type"] == "video"


def test_patch_invalid_metadata_is_rejected():
    token = signup("replay_patch_invalid")
    match = create_match(token)
    replay = create_replay(token, match["id"])

    invalid_source = client.patch(
        f"/api/matches/{match['id']}/replays/{replay['id']}",
        json={"source_type": "unknown"},
        headers=auth_headers(token),
    )
    long_filename = client.patch(
        f"/api/matches/{match['id']}/replays/{replay['id']}",
        json={"original_filename": "x" * 256},
        headers=auth_headers(token),
    )
    null_source = client.patch(
        f"/api/matches/{match['id']}/replays/{replay['id']}",
        json={"source_type": None},
        headers=auth_headers(token),
    )

    assert invalid_source.status_code == 422
    assert long_filename.status_code == 422
    assert null_source.status_code == 422
    assert "Source type cannot be null" in null_source.text


def test_filename_only_patch_omits_source_type_without_nulling_it():
    token = signup("replay_filename_only")
    match = create_match(token)
    replay = create_replay(token, match["id"], source_type="external_reference", original_filename="before")

    response = client.patch(
        f"/api/matches/{match['id']}/replays/{replay['id']}",
        json={"original_filename": " after "},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["source_type"] == "external_reference"
    assert response.json()["original_filename"] == "after"


def test_owner_can_delete_replay_without_deleting_parent_match():
    token = signup("replay_delete")
    match = create_match(token)
    replay = create_replay(token, match["id"])

    deleted = client.delete(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token))
    read_deleted = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token))
    read_match = client.get(f"/api/matches/{match['id']}", headers=auth_headers(token))

    assert deleted.status_code == 204
    assert read_deleted.status_code == 404
    assert read_match.status_code == 200


def test_account_isolation_for_nested_replay_routes():
    token_a = signup("replay_account_a")
    token_b = signup("replay_account_b")
    match_b = create_match(token_b)
    replay_b = create_replay(token_b, match_b["id"])

    list_response = client.get(f"/api/matches/{match_b['id']}/replays", headers=auth_headers(token_a))
    create_response = client.post(
        f"/api/matches/{match_b['id']}/replays",
        json={"source_type": "video", "original_filename": "steal.mp4"},
        headers=auth_headers(token_a),
    )
    read_response = client.get(f"/api/matches/{match_b['id']}/replays/{replay_b['id']}", headers=auth_headers(token_a))
    update_response = client.patch(
        f"/api/matches/{match_b['id']}/replays/{replay_b['id']}",
        json={"source_type": "video"},
        headers=auth_headers(token_a),
    )
    delete_response = client.delete(f"/api/matches/{match_b['id']}/replays/{replay_b['id']}", headers=auth_headers(token_a))

    assert list_response.status_code == 404
    assert create_response.status_code == 404
    assert read_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404


def test_legacy_match_replay_filename_is_not_changed_by_replay_api():
    token = signup("replay_legacy")
    match = create_match(token, replay_filename="legacy-placeholder.rep")

    create_replay(token, match["id"], source_type="video", original_filename="new-video.mp4")
    updated_match = client.get(f"/api/matches/{match['id']}", headers=auth_headers(token))

    assert updated_match.status_code == 200
    assert updated_match.json()["replay_filename"] == "legacy-placeholder.rep"
