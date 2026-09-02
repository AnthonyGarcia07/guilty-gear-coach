from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.routes.replays import get_frame_extraction_service, get_hud_detection_service, get_optional_storage_service, get_storage_service, get_video_inspection_service
from app.main import app
from app.services.frame_extraction import FrameExtractionError
from app.services.ggst_hud_detection import GGSTHudDetectionError, GGSTHudDetectionResult
from app.services.storage import StorageObjectMetadata
from app.services.video_inspection import VideoInspectionError, VideoMetadata

client = TestClient(app)


class FakeStorageService:
    presigned_upload_expiration_seconds = 900
    presigned_download_expiration_seconds = 300

    def __init__(
        self,
        metadata: StorageObjectMetadata | None = None,
        delete_error: Exception | None = None,
        download_error: Exception | None = None,
        download_bytes: bytes = b"fake video",
    ) -> None:
        self.metadata = metadata
        self.delete_error = delete_error
        self.download_error = download_error
        self.download_bytes = download_bytes
        self.upload_calls: list[dict] = []
        self.download_calls: list[str] = []
        self.head_calls: list[str] = []
        self.delete_calls: list[str] = []
        self.download_file_calls: list[dict] = []

    def generate_presigned_upload_url(self, storage_key: str, *, content_type: str = "video/mp4") -> str:
        self.upload_calls.append({"storage_key": storage_key, "content_type": content_type})
        return f"https://storage.example/upload/{storage_key}"

    def generate_presigned_download_url(self, storage_key: str) -> str:
        self.download_calls.append(storage_key)
        return f"https://storage.example/download/{storage_key}"

    def get_object_metadata(self, storage_key: str) -> StorageObjectMetadata | None:
        self.head_calls.append(storage_key)
        return self.metadata

    def delete_object(self, storage_key: str) -> None:
        self.delete_calls.append(storage_key)
        if self.delete_error:
            raise self.delete_error

    def download_object_to_file(self, storage_key: str, destination: str) -> None:
        self.download_file_calls.append({"storage_key": storage_key, "destination": destination})
        if self.download_error:
            raise self.download_error
        with open(destination, "wb") as video:
            video.write(self.download_bytes)


class FakeVideoInspectionService:
    def __init__(self, metadata: VideoMetadata | None = None, error: VideoInspectionError | None = None) -> None:
        self.metadata = metadata or VideoMetadata(duration_seconds=123.456, width=1920, height=1080, fps=59.94, codec="h264")
        self.error = error
        self.inspect_calls: list[str] = []

    def inspect(self, video_path: str) -> VideoMetadata:
        self.inspect_calls.append(video_path)
        if self.error:
            raise self.error
        return self.metadata


class FakeFrameExtractionService:
    def __init__(self, image_bytes: bytes = b"\xff\xd8\xff\xd9", error: FrameExtractionError | None = None) -> None:
        self.image_bytes = image_bytes
        self.error = error
        self.calls: list[dict] = []

    def extract_jpeg_frame(self, video_path: str, timestamp_seconds: float, output_path: str) -> None:
        self.calls.append({"video_path": str(video_path), "timestamp_seconds": timestamp_seconds, "output_path": str(output_path)})
        if self.error:
            raise self.error
        with open(output_path, "wb") as frame:
            frame.write(self.image_bytes)


class FakeHudDetectionService:
    def __init__(self, result: GGSTHudDetectionResult | None = None, error: GGSTHudDetectionError | None = None) -> None:
        self.result = result or GGSTHudDetectionResult(
            classification="likely_gameplay_hud",
            evidence={
                "top_left_hud": True,
                "top_right_hud": True,
                "top_center_support": True,
                "bottom_support": True,
                "transition_hint": False,
                "bilateral_top_hud": True,
            },
            measurements={
                "top_left_horizontal_edge_score": 18.4,
                "top_center_horizontal_edge_score": 15.05,
                "top_right_horizontal_edge_score": 24.41,
            },
        )
        self.error = error
        self.calls: list[dict] = []

    def detect(self, image_path: str | Path) -> GGSTHudDetectionResult:
        path = str(image_path)
        self.calls.append({"image_path": path, "exists_during_detection": Path(path).exists()})
        if self.error:
            raise self.error
        return self.result


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    yield
    app.dependency_overrides.clear()


def install_fake_storage(storage: FakeStorageService) -> FakeStorageService:
    app.dependency_overrides[get_storage_service] = lambda: storage
    app.dependency_overrides[get_optional_storage_service] = lambda: storage
    return storage


def install_fake_inspector(inspector: FakeVideoInspectionService) -> FakeVideoInspectionService:
    app.dependency_overrides[get_video_inspection_service] = lambda: inspector
    return inspector


def install_fake_frame_extractor(extractor: FakeFrameExtractionService) -> FakeFrameExtractionService:
    app.dependency_overrides[get_frame_extraction_service] = lambda: extractor
    return extractor


def install_fake_hud_detector(detector: FakeHudDetectionService) -> FakeHudDetectionService:
    app.dependency_overrides[get_hud_detection_service] = lambda: detector
    return detector


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


def init_upload(token: str, match_id: int, original_filename: str = "set.mp4", content_type: str = "video/mp4", size_bytes: int = 1024) -> dict:
    response = client.post(
        f"/api/matches/{match_id}/replays/uploads",
        json={"original_filename": original_filename, "content_type": content_type, "size_bytes": size_bytes},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    return response.json()


def create_processed_uploaded_replay(token: str, match_id: int, duration_seconds: float = 64.0) -> dict:
    upload = init_upload(token, match_id)
    replay = upload["replay"]
    confirmed = client.post(f"/api/matches/{match_id}/replays/{replay['id']}/confirm-upload", headers=auth_headers(token))
    assert confirmed.status_code == 200
    install_fake_inspector(FakeVideoInspectionService(VideoMetadata(duration_seconds=duration_seconds, width=1920, height=1080, fps=59.94, codec="h264")))
    inspected = client.post(f"/api/matches/{match_id}/replays/{replay['id']}/inspect", headers=auth_headers(token))
    assert inspected.status_code == 200
    return inspected.json()["replay"]


def test_replay_endpoints_require_authentication():
    token = signup("replay_auth")
    match = create_match(token)
    replay = create_replay(token, match["id"])

    assert client.get(f"/api/matches/{match['id']}/replays").status_code == 401
    assert client.post(f"/api/matches/{match['id']}/replays", json={"source_type": "video"}).status_code == 401
    assert client.get(f"/api/matches/{match['id']}/replays/{replay['id']}").status_code == 401
    assert client.patch(f"/api/matches/{match['id']}/replays/{replay['id']}", json={"source_type": "video"}).status_code == 401
    assert client.delete(f"/api/matches/{match['id']}/replays/{replay['id']}").status_code == 401
    assert client.post(f"/api/matches/{match['id']}/replays/uploads", json={"content_type": "video/mp4", "size_bytes": 1024}).status_code == 401
    assert client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/confirm-upload").status_code == 401
    assert client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/download-url").status_code == 401
    assert client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/inspect").status_code == 401
    assert client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/frames/sample", json={"timestamp_seconds": 1}).status_code == 401
    assert client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/hud-detection", json={"timestamp_seconds": 1}).status_code == 401


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
    assert body["storage_key"] is None
    assert body["upload_status"] == "metadata_only"
    assert body["content_type"] is None
    assert body["size_bytes"] is None
    assert body["uploaded_at"] is None
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


def test_metadata_create_rejects_client_controlled_storage_fields():
    token = signup("replay_storage_create")
    match = create_match(token)

    response = client.post(
        f"/api/matches/{match['id']}/replays",
        json={
            "source_type": "video",
            "original_filename": "set.mp4",
            "storage_key": "users/1/matches/2/replays/forged.mp4",
            "upload_status": "uploaded",
            "content_type": "video/mp4",
            "size_bytes": 100,
            "uploaded_at": "2026-08-22T12:00:00Z",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_initialize_mp4_upload_creates_pending_replay_and_presigned_put_url():
    storage = install_fake_storage(FakeStorageService())
    token = signup("replay_upload_init")
    match = create_match(token)

    response = client.post(
        f"/api/matches/{match['id']}/replays/uploads",
        json={"original_filename": " set-one.mp4 ", "content_type": "video/mp4", "size_bytes": 4096},
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    replay = body["replay"]
    assert replay["match_id"] == match["id"]
    assert replay["source_type"] == "video"
    assert replay["original_filename"] == "set-one.mp4"
    assert replay["upload_status"] == "pending_upload"
    assert replay["content_type"] == "video/mp4"
    assert replay["size_bytes"] == 4096
    assert replay["uploaded_at"] is None
    assert replay["storage_key"] == body["storage_key"]
    assert replay["storage_key"].startswith(f"users/")
    assert f"/matches/{match['id']}/replays/" in replay["storage_key"]
    assert replay["storage_key"].endswith(".mp4")
    assert body["upload_url"] == f"https://storage.example/upload/{replay['storage_key']}"
    assert body["expires_in_seconds"] == 900
    assert storage.upload_calls == [{"storage_key": replay["storage_key"], "content_type": "video/mp4"}]

    stored = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token))
    assert stored.status_code == 200
    assert stored.json()["upload_status"] == "pending_upload"


def test_initialize_mp4_upload_rejects_invalid_content_type_and_size():
    install_fake_storage(FakeStorageService())
    token = signup("replay_upload_invalid")
    match = create_match(token)

    invalid_type = client.post(
        f"/api/matches/{match['id']}/replays/uploads",
        json={"original_filename": "set.mov", "content_type": "video/quicktime", "size_bytes": 1024},
        headers=auth_headers(token),
    )
    empty_size = client.post(
        f"/api/matches/{match['id']}/replays/uploads",
        json={"original_filename": "set.mp4", "content_type": "video/mp4", "size_bytes": 0},
        headers=auth_headers(token),
    )
    oversize = client.post(
        f"/api/matches/{match['id']}/replays/uploads",
        json={"original_filename": "set.mp4", "content_type": "video/mp4", "size_bytes": 2 * 1024 * 1024 * 1024 + 1},
        headers=auth_headers(token),
    )

    assert invalid_type.status_code == 422
    assert empty_size.status_code == 422
    assert oversize.status_code == 422


def test_initialize_mp4_upload_is_account_isolated():
    install_fake_storage(FakeStorageService())
    token_a = signup("replay_upload_owner_a")
    token_b = signup("replay_upload_owner_b")
    match_b = create_match(token_b)

    response = client.post(
        f"/api/matches/{match_b['id']}/replays/uploads",
        json={"original_filename": "steal.mp4", "content_type": "video/mp4", "size_bytes": 1024},
        headers=auth_headers(token_a),
    )

    assert response.status_code == 404


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


def test_metadata_patch_rejects_client_controlled_storage_fields():
    token = signup("replay_storage_patch")
    match = create_match(token)
    replay = create_replay(token, match["id"], source_type="video", original_filename="set.mp4")

    response = client.patch(
        f"/api/matches/{match['id']}/replays/{replay['id']}",
        json={
            "storage_key": "users/1/matches/2/replays/forged.mp4",
            "upload_status": "uploaded",
            "content_type": "video/mp4",
            "size_bytes": 100,
            "uploaded_at": "2026-08-22T12:00:00Z",
        },
        headers=auth_headers(token),
    )
    after = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token))

    assert response.status_code == 422
    assert after.status_code == 200
    assert after.json()["storage_key"] is None
    assert after.json()["upload_status"] == "metadata_only"
    assert after.json()["content_type"] is None
    assert after.json()["size_bytes"] is None
    assert after.json()["uploaded_at"] is None


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


def test_confirm_upload_uses_storage_head_and_persists_trusted_metadata():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=2048, content_type="video/mp4", etag='"etag"', metadata={})))
    token = signup("replay_confirm")
    match = create_match(token)
    upload = init_upload(token, match["id"], size_bytes=1024)
    replay = upload["replay"]

    response = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/confirm-upload", headers=auth_headers(token))

    assert response.status_code == 200
    confirmed = response.json()["replay"]
    assert confirmed["upload_status"] == "uploaded"
    assert confirmed["content_type"] == "video/mp4"
    assert confirmed["size_bytes"] == 2048
    assert confirmed["uploaded_at"] is not None
    assert storage.head_calls == [replay["storage_key"]]

    stored = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token))
    assert stored.status_code == 200
    assert stored.json()["upload_status"] == "uploaded"
    assert stored.json()["size_bytes"] == 2048


def test_confirm_upload_is_safe_to_repeat():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=2048, content_type="video/mp4", etag='"etag"', metadata={})))
    token = signup("replay_confirm_repeat")
    match = create_match(token)
    upload = init_upload(token, match["id"])
    replay = upload["replay"]

    first = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/confirm-upload", headers=auth_headers(token))
    second = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/confirm-upload", headers=auth_headers(token))

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["replay"]["upload_status"] == "uploaded"


def test_confirm_upload_rejects_missing_or_invalid_object_metadata():
    token = signup("replay_confirm_invalid")
    match = create_match(token)

    missing_storage = install_fake_storage(FakeStorageService(None))
    missing_upload = init_upload(token, match["id"], original_filename="missing.mp4")
    missing = client.post(f"/api/matches/{match['id']}/replays/{missing_upload['replay']['id']}/confirm-upload", headers=auth_headers(token))
    assert missing.status_code == 404
    assert missing_storage.head_calls == [missing_upload["storage_key"]]

    bad_type_storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/webm", etag=None, metadata={})))
    bad_type_upload = init_upload(token, match["id"], original_filename="bad-type.mp4")
    bad_type = client.post(f"/api/matches/{match['id']}/replays/{bad_type_upload['replay']['id']}/confirm-upload", headers=auth_headers(token))
    assert bad_type.status_code == 422
    assert bad_type_storage.head_calls == [bad_type_upload["storage_key"]]

    bad_size_storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=0, content_type="video/mp4", etag=None, metadata={})))
    bad_size_upload = init_upload(token, match["id"], original_filename="bad-size.mp4")
    bad_size = client.post(f"/api/matches/{match['id']}/replays/{bad_size_upload['replay']['id']}/confirm-upload", headers=auth_headers(token))
    assert bad_size.status_code == 422
    assert bad_size_storage.head_calls == [bad_size_upload["storage_key"]]

    after_bad_size = client.get(f"/api/matches/{match['id']}/replays/{bad_size_upload['replay']['id']}", headers=auth_headers(token))
    assert after_bad_size.status_code == 200
    assert after_bad_size.json()["upload_status"] == "pending_upload"
    assert after_bad_size.json()["uploaded_at"] is None


def test_confirm_upload_requires_replay_with_storage_key():
    install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    token = signup("replay_confirm_no_key")
    match = create_match(token)
    replay = create_replay(token, match["id"], source_type="video", original_filename="metadata-only.mp4")

    response = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/confirm-upload", headers=auth_headers(token))

    assert response.status_code == 409


def test_confirm_upload_is_account_isolated():
    install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    token_a = signup("replay_confirm_owner_a")
    token_b = signup("replay_confirm_owner_b")
    match_b = create_match(token_b)
    upload_b = init_upload(token_b, match_b["id"])

    response = client.post(f"/api/matches/{match_b['id']}/replays/{upload_b['replay']['id']}/confirm-upload", headers=auth_headers(token_a))

    assert response.status_code == 404


def test_download_url_requires_confirmed_upload():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    token = signup("replay_download_pending")
    match = create_match(token)
    upload = init_upload(token, match["id"])
    replay = upload["replay"]

    response = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/download-url", headers=auth_headers(token))

    assert response.status_code == 409
    assert storage.download_calls == []


def test_download_url_is_generated_for_confirmed_upload():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    token = signup("replay_download")
    match = create_match(token)
    upload = init_upload(token, match["id"])
    replay = upload["replay"]
    confirmed = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/confirm-upload", headers=auth_headers(token))
    assert confirmed.status_code == 200

    response = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/download-url", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json() == {
        "download_url": f"https://storage.example/download/{replay['storage_key']}",
        "expires_in_seconds": 300,
    }
    assert storage.download_calls == [replay["storage_key"]]


def test_download_url_is_account_isolated():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    token_a = signup("replay_download_owner_a")
    token_b = signup("replay_download_owner_b")
    match_b = create_match(token_b)
    upload_b = init_upload(token_b, match_b["id"])
    replay_b = upload_b["replay"]
    confirmed = client.post(f"/api/matches/{match_b['id']}/replays/{replay_b['id']}/confirm-upload", headers=auth_headers(token_b))
    assert confirmed.status_code == 200

    response = client.post(f"/api/matches/{match_b['id']}/replays/{replay_b['id']}/download-url", headers=auth_headers(token_a))

    assert response.status_code == 404
    assert storage.download_calls == []


def test_metadata_only_and_pending_replays_cannot_be_inspected():
    install_fake_storage(FakeStorageService())
    install_fake_inspector(FakeVideoInspectionService())
    token = signup("replay_inspect_unavailable")
    match = create_match(token)
    metadata_only = create_replay(token, match["id"], source_type="video", original_filename="metadata-only.mp4")
    pending = init_upload(token, match["id"], original_filename="pending.mp4")

    metadata_response = client.post(f"/api/matches/{match['id']}/replays/{metadata_only['id']}/inspect", headers=auth_headers(token))
    pending_response = client.post(f"/api/matches/{match['id']}/replays/{pending['replay']['id']}/inspect", headers=auth_headers(token))

    assert metadata_response.status_code == 409
    assert pending_response.status_code == 409


def test_confirmed_uploaded_replay_can_be_inspected_and_persists_video_metadata():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    inspector = install_fake_inspector(FakeVideoInspectionService(VideoMetadata(duration_seconds=93.25, width=1280, height=720, fps=60.0, codec="h264")))
    token = signup("replay_inspect_success")
    match = create_match(token)
    upload = init_upload(token, match["id"])
    replay = upload["replay"]
    confirmed = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/confirm-upload", headers=auth_headers(token))
    assert confirmed.status_code == 200

    response = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/inspect", headers=auth_headers(token))
    stored = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token))

    assert response.status_code == 200
    inspected = response.json()["replay"]
    assert inspected["processing_status"] == "processed"
    assert inspected["processing_error"] is None
    assert inspected["metadata_inspected_at"] is not None
    assert inspected["video_duration_seconds"] == 93.25
    assert inspected["video_width"] == 1280
    assert inspected["video_height"] == 720
    assert inspected["video_fps"] == 60.0
    assert inspected["video_codec"] == "h264"
    assert storage.download_file_calls[0]["storage_key"] == replay["storage_key"]
    assert len(inspector.inspect_calls) == 1
    assert stored.json()["processing_status"] == "processed"


def test_inspect_replay_is_account_isolated():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    install_fake_inspector(FakeVideoInspectionService())
    token_a = signup("replay_inspect_owner_a")
    token_b = signup("replay_inspect_owner_b")
    match_b = create_match(token_b)
    upload_b = init_upload(token_b, match_b["id"])
    confirmed = client.post(f"/api/matches/{match_b['id']}/replays/{upload_b['replay']['id']}/confirm-upload", headers=auth_headers(token_b))
    assert confirmed.status_code == 200

    response = client.post(f"/api/matches/{match_b['id']}/replays/{upload_b['replay']['id']}/inspect", headers=auth_headers(token_a))

    assert response.status_code == 404
    assert storage.download_file_calls == []


def test_inspection_failure_persists_failed_state_and_safe_error():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    install_fake_inspector(FakeVideoInspectionService(error=VideoInspectionError("No usable video stream was found.")))
    token = signup("replay_inspect_fail")
    match = create_match(token)
    upload = init_upload(token, match["id"])
    replay = upload["replay"]
    confirmed = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/confirm-upload", headers=auth_headers(token))
    assert confirmed.status_code == 200

    response = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/inspect", headers=auth_headers(token))
    stored = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token)).json()

    assert response.status_code == 422
    assert response.json()["detail"] == "No usable video stream was found."
    assert stored["processing_status"] == "failed"
    assert stored["processing_error"] == "No usable video stream was found."
    assert stored["upload_status"] == "uploaded"


def test_inspection_timeout_persists_failed_state_and_safe_error():
    install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    install_fake_inspector(FakeVideoInspectionService(error=VideoInspectionError("Video metadata inspection timed out.")))
    token = signup("replay_inspect_timeout")
    match = create_match(token)
    upload = init_upload(token, match["id"])
    replay = upload["replay"]
    confirmed = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/confirm-upload", headers=auth_headers(token))
    assert confirmed.status_code == 200

    response = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/inspect", headers=auth_headers(token))
    stored = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token)).json()

    assert response.status_code == 422
    assert response.json()["detail"] == "Video metadata inspection timed out."
    assert stored["processing_status"] == "failed"
    assert stored["processing_error"] == "Video metadata inspection timed out."


def test_reinspection_replaces_old_technical_metadata():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    inspector = install_fake_inspector(FakeVideoInspectionService(VideoMetadata(duration_seconds=90.0, width=1280, height=720, fps=60.0, codec="h264")))
    token = signup("replay_reinspect")
    match = create_match(token)
    upload = init_upload(token, match["id"])
    replay = upload["replay"]
    confirmed = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/confirm-upload", headers=auth_headers(token))
    assert confirmed.status_code == 200
    first = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/inspect", headers=auth_headers(token))
    assert first.status_code == 200

    inspector.metadata = VideoMetadata(duration_seconds=120.0, width=1920, height=1080, fps=59.94, codec="hevc")
    second = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/inspect", headers=auth_headers(token))

    assert second.status_code == 200
    inspected = second.json()["replay"]
    assert inspected["video_duration_seconds"] == 120.0
    assert inspected["video_width"] == 1920
    assert inspected["video_height"] == 1080
    assert inspected["video_fps"] == 59.94
    assert inspected["video_codec"] == "hevc"
    assert len(storage.download_file_calls) == 2


def test_storage_access_failure_during_inspection_is_safe():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={}), download_error=RuntimeError("R2 unavailable")))
    inspector = install_fake_inspector(FakeVideoInspectionService())
    token = signup("replay_inspect_storage_fail")
    match = create_match(token)
    upload = init_upload(token, match["id"])
    replay = upload["replay"]
    confirmed = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/confirm-upload", headers=auth_headers(token))
    assert confirmed.status_code == 200

    response = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/inspect", headers=auth_headers(token))
    stored = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token)).json()

    assert response.status_code == 502
    assert stored["processing_status"] == "failed"
    assert stored["processing_error"] == "Unable to access replay video for inspection."
    assert storage.download_file_calls[0]["storage_key"] == replay["storage_key"]
    assert inspector.inspect_calls == []


def test_metadata_only_and_pending_replays_cannot_sample_frames():
    install_fake_storage(FakeStorageService())
    install_fake_frame_extractor(FakeFrameExtractionService())
    token = signup("replay_sample_unavailable")
    match = create_match(token)
    metadata_only = create_replay(token, match["id"], source_type="video", original_filename="metadata-only.mp4")
    pending = init_upload(token, match["id"], original_filename="pending.mp4")

    metadata_response = client.post(
        f"/api/matches/{match['id']}/replays/{metadata_only['id']}/frames/sample",
        json={"timestamp_seconds": 1},
        headers=auth_headers(token),
    )
    pending_response = client.post(
        f"/api/matches/{match['id']}/replays/{pending['replay']['id']}/frames/sample",
        json={"timestamp_seconds": 1},
        headers=auth_headers(token),
    )

    assert metadata_response.status_code == 409
    assert metadata_response.json()["detail"] == "Replay upload must be confirmed before frame sampling."
    assert pending_response.status_code == 409


def test_uploaded_replay_must_be_inspected_before_sampling_frames():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    install_fake_frame_extractor(FakeFrameExtractionService())
    token = signup("replay_sample_not_inspected")
    match = create_match(token)
    upload = init_upload(token, match["id"])
    replay = upload["replay"]
    confirmed = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/confirm-upload", headers=auth_headers(token))
    assert confirmed.status_code == 200

    response = client.post(
        f"/api/matches/{match['id']}/replays/{replay['id']}/frames/sample",
        json={"timestamp_seconds": 1},
        headers=auth_headers(token),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Replay video metadata must be inspected before frame sampling."
    assert storage.download_file_calls == []


def test_processed_uploaded_replay_can_sample_frame_as_jpeg():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    extractor = install_fake_frame_extractor(FakeFrameExtractionService(image_bytes=b"\xff\xd8sample\xff\xd9"))
    token = signup("replay_sample_success")
    match = create_match(token)
    replay = create_processed_uploaded_replay(token, match["id"], duration_seconds=64.0)
    storage.download_file_calls.clear()

    response = client.post(
        f"/api/matches/{match['id']}/replays/{replay['id']}/frames/sample",
        json={"timestamp_seconds": 10.25},
        headers=auth_headers(token),
    )
    stored = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token)).json()

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content == b"\xff\xd8sample\xff\xd9"
    assert storage.download_file_calls[0]["storage_key"] == replay["storage_key"]
    assert extractor.calls[0]["timestamp_seconds"] == 10.25
    assert stored["upload_status"] == "uploaded"
    assert stored["processing_status"] == "processed"
    assert stored["video_duration_seconds"] == 64.0


def test_sample_frame_is_account_isolated():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    extractor = install_fake_frame_extractor(FakeFrameExtractionService())
    token_a = signup("replay_sample_owner_a")
    token_b = signup("replay_sample_owner_b")
    match_b = create_match(token_b)
    replay_b = create_processed_uploaded_replay(token_b, match_b["id"], duration_seconds=64.0)
    storage.download_file_calls.clear()

    response = client.post(
        f"/api/matches/{match_b['id']}/replays/{replay_b['id']}/frames/sample",
        json={"timestamp_seconds": 5},
        headers=auth_headers(token_a),
    )

    assert response.status_code == 404
    assert storage.download_file_calls == []
    assert extractor.calls == []


def test_sample_frame_rejects_invalid_timestamps_before_downloading():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    install_fake_frame_extractor(FakeFrameExtractionService())
    token = signup("replay_sample_bad_timestamp")
    match = create_match(token)
    replay = create_processed_uploaded_replay(token, match["id"], duration_seconds=64.0)
    storage.download_file_calls.clear()

    negative = client.post(
        f"/api/matches/{match['id']}/replays/{replay['id']}/frames/sample",
        json={"timestamp_seconds": -1},
        headers=auth_headers(token),
    )
    at_end = client.post(
        f"/api/matches/{match['id']}/replays/{replay['id']}/frames/sample",
        json={"timestamp_seconds": 64},
        headers=auth_headers(token),
    )
    beyond_end = client.post(
        f"/api/matches/{match['id']}/replays/{replay['id']}/frames/sample",
        json={"timestamp_seconds": 65},
        headers=auth_headers(token),
    )

    assert negative.status_code == 422
    assert at_end.status_code == 422
    assert at_end.json()["detail"] == "Timestamp must be before the end of the video."
    assert beyond_end.status_code == 422
    assert storage.download_file_calls == []


def test_sample_frame_storage_failure_returns_safe_error_without_state_changes():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    extractor = install_fake_frame_extractor(FakeFrameExtractionService())
    token = signup("replay_sample_storage_fail")
    match = create_match(token)
    replay = create_processed_uploaded_replay(token, match["id"], duration_seconds=64.0)
    storage.download_error = RuntimeError("R2 unavailable")
    storage.download_file_calls.clear()

    response = client.post(
        f"/api/matches/{match['id']}/replays/{replay['id']}/frames/sample",
        json={"timestamp_seconds": 10},
        headers=auth_headers(token),
    )
    stored = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token)).json()

    assert response.status_code == 502
    assert response.json()["detail"] == "Unable to sample replay frame."
    assert storage.download_file_calls[0]["storage_key"] == replay["storage_key"]
    assert extractor.calls == []
    assert stored["upload_status"] == "uploaded"
    assert stored["processing_status"] == "processed"


def test_sample_frame_extraction_failure_returns_safe_error_without_state_changes():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    extractor = install_fake_frame_extractor(FakeFrameExtractionService(error=FrameExtractionError("Frame extraction timed out.")))
    token = signup("replay_sample_extract_fail")
    match = create_match(token)
    replay = create_processed_uploaded_replay(token, match["id"], duration_seconds=64.0)
    storage.download_file_calls.clear()

    response = client.post(
        f"/api/matches/{match['id']}/replays/{replay['id']}/frames/sample",
        json={"timestamp_seconds": 10},
        headers=auth_headers(token),
    )
    stored = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token)).json()

    assert response.status_code == 422
    assert response.json()["detail"] == "Frame extraction timed out."
    assert storage.download_file_calls[0]["storage_key"] == replay["storage_key"]
    assert len(extractor.calls) == 1
    assert stored["upload_status"] == "uploaded"
    assert stored["processing_status"] == "processed"


@pytest.mark.parametrize(
    ("classification", "evidence"),
    [
        (
            "likely_gameplay_hud",
            {
                "top_left_hud": True,
                "top_right_hud": True,
                "top_center_support": True,
                "bottom_support": True,
                "transition_hint": False,
                "bilateral_top_hud": True,
            },
        ),
        (
            "unknown",
            {
                "top_left_hud": False,
                "top_right_hud": False,
                "top_center_support": False,
                "bottom_support": True,
                "transition_hint": True,
                "bilateral_top_hud": False,
            },
        ),
        (
            "not_gameplay_hud",
            {
                "top_left_hud": False,
                "top_right_hud": False,
                "top_center_support": False,
                "bottom_support": False,
                "transition_hint": False,
                "bilateral_top_hud": False,
            },
        ),
    ],
)
def test_detect_replay_hud_returns_structured_detection_response(classification: str, evidence: dict[str, bool]):
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    extractor = install_fake_frame_extractor(FakeFrameExtractionService(image_bytes=b"\xff\xd8sample\xff\xd9"))
    detector = install_fake_hud_detector(FakeHudDetectionService(GGSTHudDetectionResult(
        classification=classification,
        evidence=evidence,
        measurements={
            "top_left_horizontal_edge_score": 18.4,
            "top_center_horizontal_edge_score": 15.05,
            "top_right_horizontal_edge_score": 24.41,
            "top_center_stddev": 73.88,
        },
    )))
    token = signup(f"replay_hud_{classification}")
    match = create_match(token)
    replay = create_processed_uploaded_replay(token, match["id"], duration_seconds=64.0)
    storage.download_file_calls.clear()

    response = client.post(
        f"/api/matches/{match['id']}/replays/{replay['id']}/hud-detection",
        json={"timestamp_seconds": 15},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["timestamp_seconds"] == 15
    assert body["classification"] == classification
    assert body["evidence"] == evidence
    assert body["measurements"]["top_left_horizontal_edge_score"] == 18.4
    assert body["measurements"]["top_center_stddev"] == 73.88
    assert storage.download_file_calls[0]["storage_key"] == replay["storage_key"]
    assert extractor.calls[0]["timestamp_seconds"] == 15
    assert detector.calls[0]["exists_during_detection"] is True
    assert Path(detector.calls[0]["image_path"]).exists() is False
    assert Path(storage.download_file_calls[0]["destination"]).exists() is False


def test_detect_replay_hud_is_account_isolated():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    extractor = install_fake_frame_extractor(FakeFrameExtractionService())
    detector = install_fake_hud_detector(FakeHudDetectionService())
    token_a = signup("replay_hud_owner_a")
    token_b = signup("replay_hud_owner_b")
    match_b = create_match(token_b)
    replay_b = create_processed_uploaded_replay(token_b, match_b["id"], duration_seconds=64.0)
    storage.download_file_calls.clear()

    response = client.post(
        f"/api/matches/{match_b['id']}/replays/{replay_b['id']}/hud-detection",
        json={"timestamp_seconds": 5},
        headers=auth_headers(token_a),
    )

    assert response.status_code == 404
    assert storage.download_file_calls == []
    assert extractor.calls == []
    assert detector.calls == []


def test_detect_replay_hud_reuses_sample_timestamp_validation():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    install_fake_frame_extractor(FakeFrameExtractionService())
    install_fake_hud_detector(FakeHudDetectionService())
    token = signup("replay_hud_bad_timestamp")
    match = create_match(token)
    replay = create_processed_uploaded_replay(token, match["id"], duration_seconds=64.0)
    storage.download_file_calls.clear()

    negative = client.post(
        f"/api/matches/{match['id']}/replays/{replay['id']}/hud-detection",
        json={"timestamp_seconds": -1},
        headers=auth_headers(token),
    )
    at_end = client.post(
        f"/api/matches/{match['id']}/replays/{replay['id']}/hud-detection",
        json={"timestamp_seconds": 64},
        headers=auth_headers(token),
    )

    assert negative.status_code == 422
    assert at_end.status_code == 422
    assert at_end.json()["detail"] == "Timestamp must be before the end of the video."
    assert storage.download_file_calls == []


def test_detect_replay_hud_reuses_replay_ready_validation():
    install_fake_storage(FakeStorageService())
    install_fake_frame_extractor(FakeFrameExtractionService())
    install_fake_hud_detector(FakeHudDetectionService())
    token = signup("replay_hud_unavailable")
    match = create_match(token)
    metadata_only = create_replay(token, match["id"], source_type="video", original_filename="metadata-only.mp4")
    pending = init_upload(token, match["id"], original_filename="pending.mp4")

    metadata_response = client.post(
        f"/api/matches/{match['id']}/replays/{metadata_only['id']}/hud-detection",
        json={"timestamp_seconds": 1},
        headers=auth_headers(token),
    )
    pending_response = client.post(
        f"/api/matches/{match['id']}/replays/{pending['replay']['id']}/hud-detection",
        json={"timestamp_seconds": 1},
        headers=auth_headers(token),
    )

    assert metadata_response.status_code == 409
    assert metadata_response.json()["detail"] == "Replay upload must be confirmed before frame sampling."
    assert pending_response.status_code == 409


def test_detect_replay_hud_maps_frame_extraction_failure_safely():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    extractor = install_fake_frame_extractor(FakeFrameExtractionService(error=FrameExtractionError("Frame extraction failed.")))
    detector = install_fake_hud_detector(FakeHudDetectionService())
    token = signup("replay_hud_extract_fail")
    match = create_match(token)
    replay = create_processed_uploaded_replay(token, match["id"], duration_seconds=64.0)
    storage.download_file_calls.clear()

    response = client.post(
        f"/api/matches/{match['id']}/replays/{replay['id']}/hud-detection",
        json={"timestamp_seconds": 10},
        headers=auth_headers(token),
    )
    stored = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token)).json()

    assert response.status_code == 422
    assert response.json()["detail"] == "Frame extraction failed."
    assert len(extractor.calls) == 1
    assert detector.calls == []
    assert stored["upload_status"] == "uploaded"
    assert stored["processing_status"] == "processed"


def test_detect_replay_hud_maps_detector_failure_safely_and_cleans_up_temp_files():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    extractor = install_fake_frame_extractor(FakeFrameExtractionService(image_bytes=b"\xff\xd8sample\xff\xd9"))
    detector = install_fake_hud_detector(FakeHudDetectionService(error=GGSTHudDetectionError("HUD detection image could not be read.")))
    token = signup("replay_hud_detector_fail")
    match = create_match(token)
    replay = create_processed_uploaded_replay(token, match["id"], duration_seconds=64.0)
    storage.download_file_calls.clear()

    response = client.post(
        f"/api/matches/{match['id']}/replays/{replay['id']}/hud-detection",
        json={"timestamp_seconds": 10},
        headers=auth_headers(token),
    )
    stored = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token)).json()

    assert response.status_code == 422
    assert response.json()["detail"] == "HUD detection image could not be read."
    assert detector.calls[0]["exists_during_detection"] is True
    assert Path(detector.calls[0]["image_path"]).exists() is False
    assert Path(storage.download_file_calls[0]["destination"]).exists() is False
    assert stored["upload_status"] == "uploaded"
    assert stored["processing_status"] == "processed"


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


def test_delete_uploaded_replay_removes_storage_object_before_db_row():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    token = signup("replay_delete_uploaded")
    match = create_match(token)
    upload = init_upload(token, match["id"])
    replay = upload["replay"]
    confirmed = client.post(f"/api/matches/{match['id']}/replays/{replay['id']}/confirm-upload", headers=auth_headers(token))
    assert confirmed.status_code == 200

    deleted = client.delete(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token))
    read_deleted = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token))

    assert deleted.status_code == 204
    assert storage.delete_calls == [replay["storage_key"]]
    assert read_deleted.status_code == 404


def test_delete_replay_without_storage_key_skips_storage_cleanup():
    storage = install_fake_storage(FakeStorageService())
    token = signup("replay_delete_no_key")
    match = create_match(token)
    replay = create_replay(token, match["id"], source_type="video", original_filename="metadata-only.mp4")

    deleted = client.delete(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token))
    read_deleted = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token))

    assert deleted.status_code == 204
    assert storage.delete_calls == []
    assert read_deleted.status_code == 404


def test_delete_replay_keeps_db_row_when_storage_cleanup_fails():
    storage = install_fake_storage(FakeStorageService(delete_error=RuntimeError("R2 unavailable")))
    token = signup("replay_delete_storage_fail")
    match = create_match(token)
    upload = init_upload(token, match["id"])
    replay = upload["replay"]

    deleted = client.delete(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token))
    still_exists = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token))

    assert deleted.status_code == 502
    assert storage.delete_calls == [replay["storage_key"]]
    assert still_exists.status_code == 200


def test_delete_replay_treats_missing_storage_object_as_successful_cleanup():
    storage = install_fake_storage(FakeStorageService())
    token = signup("replay_delete_missing_object")
    match = create_match(token)
    upload = init_upload(token, match["id"])
    replay = upload["replay"]

    deleted = client.delete(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token))
    read_deleted = client.get(f"/api/matches/{match['id']}/replays/{replay['id']}", headers=auth_headers(token))

    assert deleted.status_code == 204
    assert storage.delete_calls == [replay["storage_key"]]
    assert read_deleted.status_code == 404


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


def test_delete_match_removes_all_replay_storage_objects_before_cascade():
    storage = install_fake_storage(FakeStorageService())
    token = signup("match_delete_storage")
    match = create_match(token)
    first = init_upload(token, match["id"], original_filename="one.mp4")
    second = init_upload(token, match["id"], original_filename="two.mp4")

    deleted = client.delete(f"/api/matches/{match['id']}", headers=auth_headers(token))
    read_match = client.get(f"/api/matches/{match['id']}", headers=auth_headers(token))
    read_first = client.get(f"/api/matches/{match['id']}/replays/{first['replay']['id']}", headers=auth_headers(token))
    read_second = client.get(f"/api/matches/{match['id']}/replays/{second['replay']['id']}", headers=auth_headers(token))

    assert deleted.status_code == 204
    assert sorted(storage.delete_calls) == sorted([first["storage_key"], second["storage_key"]])
    assert read_match.status_code == 404
    assert read_first.status_code == 404
    assert read_second.status_code == 404


def test_delete_match_cleans_only_replays_with_storage_keys():
    storage = install_fake_storage(FakeStorageService(StorageObjectMetadata(content_length=1024, content_type="video/mp4", etag=None, metadata={})))
    token = signup("match_delete_mixed_storage")
    match = create_match(token)
    uploaded = init_upload(token, match["id"], original_filename="uploaded.mp4")
    confirmed = client.post(f"/api/matches/{match['id']}/replays/{uploaded['replay']['id']}/confirm-upload", headers=auth_headers(token))
    assert confirmed.status_code == 200
    pending = init_upload(token, match["id"], original_filename="pending.mp4")
    metadata_only = create_replay(token, match["id"], source_type="external_reference", original_filename="https://example.com")

    deleted = client.delete(f"/api/matches/{match['id']}", headers=auth_headers(token))
    read_metadata_only = client.get(f"/api/matches/{match['id']}/replays/{metadata_only['id']}", headers=auth_headers(token))

    assert deleted.status_code == 204
    assert sorted(storage.delete_calls) == sorted([uploaded["storage_key"], pending["storage_key"]])
    assert read_metadata_only.status_code == 404


def test_delete_match_keeps_match_and_replays_when_storage_cleanup_fails():
    storage = install_fake_storage(FakeStorageService(delete_error=RuntimeError("R2 unavailable")))
    token = signup("match_delete_storage_fail")
    match = create_match(token)
    upload = init_upload(token, match["id"], original_filename="blocked.mp4")
    metadata_only = create_replay(token, match["id"], source_type="external_reference", original_filename="https://example.com")

    deleted = client.delete(f"/api/matches/{match['id']}", headers=auth_headers(token))
    read_match = client.get(f"/api/matches/{match['id']}", headers=auth_headers(token))
    read_upload = client.get(f"/api/matches/{match['id']}/replays/{upload['replay']['id']}", headers=auth_headers(token))
    read_metadata_only = client.get(f"/api/matches/{match['id']}/replays/{metadata_only['id']}", headers=auth_headers(token))

    assert deleted.status_code == 502
    assert storage.delete_calls == [upload["storage_key"]]
    assert read_match.status_code == 200
    assert read_upload.status_code == 200
    assert read_metadata_only.status_code == 200


def test_legacy_match_replay_filename_is_not_changed_by_replay_api():
    token = signup("replay_legacy")
    match = create_match(token, replay_filename="legacy-placeholder.rep")

    create_replay(token, match["id"], source_type="video", original_filename="new-video.mp4")
    updated_match = client.get(f"/api/matches/{match['id']}", headers=auth_headers(token))

    assert updated_match.status_code == 200
    assert updated_match.json()["replay_filename"] == "legacy-placeholder.rep"
