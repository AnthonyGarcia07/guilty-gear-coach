"""Coordinate the HTTP workflow for replay records and private replay videos.

Routes are the boundary between HTTP and the rest of the backend. They read
validated request data, check ownership, choose status codes, call storage or
video services, update the database, and return response schemas.

Every replay action is authorized through ``Replay -> Match -> User``. The
ownership check happens before storage or video work so one user cannot learn
about or process another user's replay.
"""

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.models import Match, Replay, User
from app.schemas.replay import (
    ReplayCreate,
    ReplayDownloadUrlResponse,
    ReplayFrameSampleRequest,
    ReplayHudDetectionBatchRequest,
    ReplayHudDetectionBatchResponse,
    ReplayHudDetectionResponse,
    ReplayRead,
    ReplayInspectResponse,
    ReplayUpdate,
    ReplayUploadConfirmResponse,
    ReplayUploadInit,
    ReplayUploadInitResponse,
)
from app.services.storage import S3CompatibleStorageService, StorageConfigurationError
from app.services.frame_extraction import FFmpegFrameExtractionService, FrameExtractionError
from app.services.ggst_hud_detection import GGSTHudDetectionError, GGSTHudDetectionService
from app.services.video_inspection import FFprobeVideoInspectionService, VideoInspectionError

router = APIRouter(prefix="/matches/{match_id}/replays", tags=["replays"])


def get_owned_match(match_id: int, current_user: User, db: Session) -> Match:
    """Find a match only when it belongs to the signed-in user.

    Returning the same 404 for a missing match and another user's match avoids
    revealing that another user's resource exists.
    """

    match = db.scalar(select(Match).where(Match.id == match_id, Match.owner_id == current_user.id))
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return match


def get_match_replay(match_id: int, replay_id: int, db: Session) -> Replay:
    """Find a replay inside the match that was already authorized above."""

    replay = db.scalar(select(Replay).where(Replay.id == replay_id, Replay.match_id == match_id))
    if not replay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Replay not found")
    return replay


def get_storage_service(settings: Settings = Depends(get_settings)) -> S3CompatibleStorageService:
    """Build the storage service and turn missing settings into a safe HTTP error."""

    try:
        return S3CompatibleStorageService.from_settings(settings)
    except StorageConfigurationError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Object storage is not configured.") from error


def get_optional_storage_service(settings: Settings = Depends(get_settings)) -> S3CompatibleStorageService | None:
    """Return storage when configured, but allow metadata-only deletion without it."""

    try:
        return S3CompatibleStorageService.from_settings(settings)
    except StorageConfigurationError:
        return None


def get_video_inspection_service() -> FFprobeVideoInspectionService:
    return FFprobeVideoInspectionService()


def get_frame_extraction_service() -> FFmpegFrameExtractionService:
    return FFmpegFrameExtractionService()


def get_hud_detection_service() -> GGSTHudDetectionService:
    return GGSTHudDetectionService()


def delete_storage_object_or_raise(storage_key: str | None, storage: S3CompatibleStorageService | None) -> None:
    """Delete a stored video and translate provider errors into safe HTTP errors.

    The database row is deliberately kept when object deletion fails. This lets
    the operation be retried instead of leaving a private file with no record
    pointing to it.
    """

    if not storage_key:
        return
    if storage is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Object storage is not configured.")
    try:
        storage.delete_object(storage_key)
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to delete replay object from storage.") from error


def storage_key_for_replay(user_id: int, match_id: int) -> str:
    """Create a unique storage key grouped by owner and match.

    The random UUID prevents two uploads with the same filename from colliding.
    The key is an internal identifier, not a public download address.
    """

    return f"users/{user_id}/matches/{match_id}/replays/{uuid4().hex}.mp4"


def validate_mp4_size(size_bytes: int | None, max_size: int) -> int:
    if size_bytes is None or size_bytes <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="MP4 size must be greater than 0 bytes.")
    if size_bytes > max_size:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"MP4 size must be {max_size} bytes or less.")
    return size_bytes


def validate_mp4_content_type(content_type: str | None) -> str:
    if content_type != "video/mp4":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Content type must be video/mp4.")
    return content_type


@router.get("", response_model=list[ReplayRead])
def list_replays(match_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Replay]:
    get_owned_match(match_id, current_user, db)
    return list(db.scalars(select(Replay).where(Replay.match_id == match_id).order_by(Replay.created_at.asc(), Replay.id.asc())))


@router.post("", response_model=ReplayRead, status_code=status.HTTP_201_CREATED)
def create_replay(match_id: int, payload: ReplayCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Replay:
    get_owned_match(match_id, current_user, db)
    replay = Replay(match_id=match_id, **payload.model_dump())
    db.add(replay)
    db.commit()
    db.refresh(replay)
    return replay


@router.post("/uploads", response_model=ReplayUploadInitResponse, status_code=status.HTTP_201_CREATED)
def initialize_replay_upload(
    match_id: int,
    payload: ReplayUploadInit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    storage: S3CompatibleStorageService = Depends(get_storage_service),
) -> ReplayUploadInitResponse:
    """Start the two-system upload workflow.

    First create a pending PostgreSQL record, then give the browser a temporary
    URL that uploads the large MP4 directly to R2. Sending large video bytes
    directly avoids using the FastAPI server as an unnecessary file relay.
    """

    match = get_owned_match(match_id, current_user, db)
    validate_mp4_content_type(payload.content_type)
    declared_size = validate_mp4_size(payload.size_bytes, settings.max_mp4_upload_size_bytes)
    storage_key = storage_key_for_replay(current_user.id, match.id)
    replay = Replay(
        match_id=match.id,
        source_type="video",
        original_filename=payload.original_filename,
        storage_key=storage_key,
        upload_status="pending_upload",
        content_type=payload.content_type,
        size_bytes=declared_size,
    )
    db.add(replay)
    db.commit()
    db.refresh(replay)
    upload_url = storage.generate_presigned_upload_url(storage_key, content_type=payload.content_type)
    return ReplayUploadInitResponse(
        replay=replay,
        upload_url=upload_url,
        storage_key=storage_key,
        expires_in_seconds=storage.presigned_upload_expiration_seconds,
    )


@router.get("/{replay_id}", response_model=ReplayRead)
def get_replay(match_id: int, replay_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Replay:
    get_owned_match(match_id, current_user, db)
    return get_match_replay(match_id, replay_id, db)


@router.post("/{replay_id}/confirm-upload", response_model=ReplayUploadConfirmResponse)
def confirm_replay_upload(
    match_id: int,
    replay_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    storage: S3CompatibleStorageService = Depends(get_storage_service),
) -> ReplayUploadConfirmResponse:
    """Verify the R2 object before marking the replay as uploaded.

    The browser saying "upload complete" is not trusted. The backend asks R2
    for the actual content type and size, validates them, and stores those
    trusted values in PostgreSQL.
    """

    get_owned_match(match_id, current_user, db)
    replay = get_match_replay(match_id, replay_id, db)
    if not replay.storage_key:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Replay does not have a storage object to confirm.")
    metadata = storage.get_object_metadata(replay.storage_key)
    if metadata is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded object was not found in storage.")
    content_type = validate_mp4_content_type(metadata.content_type)
    size_bytes = validate_mp4_size(metadata.content_length, settings.max_mp4_upload_size_bytes)
    replay.upload_status = "uploaded"
    replay.content_type = content_type
    replay.size_bytes = size_bytes
    replay.uploaded_at = datetime.now(timezone.utc)
    replay.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(replay)
    return ReplayUploadConfirmResponse(replay=replay)


@router.post("/{replay_id}/download-url", response_model=ReplayDownloadUrlResponse)
def create_replay_download_url(
    match_id: int,
    replay_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: S3CompatibleStorageService = Depends(get_storage_service),
) -> ReplayDownloadUrlResponse:
    """Return short-lived download access to an owned, confirmed upload."""

    get_owned_match(match_id, current_user, db)
    replay = get_match_replay(match_id, replay_id, db)
    if replay.upload_status != "uploaded" or not replay.storage_key:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Replay upload has not been confirmed.")
    return ReplayDownloadUrlResponse(
        download_url=storage.generate_presigned_download_url(replay.storage_key),
        expires_in_seconds=storage.presigned_download_expiration_seconds,
    )


@router.post("/{replay_id}/inspect", response_model=ReplayInspectResponse)
def inspect_replay_video_metadata(
    match_id: int,
    replay_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: S3CompatibleStorageService = Depends(get_storage_service),
    inspector: FFprobeVideoInspectionService = Depends(get_video_inspection_service),
) -> ReplayInspectResponse:
    """Inspect a confirmed video and save its technical metadata.

    The route records ``processing`` before starting external work. It then
    downloads the private MP4 to a temporary folder, asks ffprobe for metadata,
    and saves either the successful result or a safe failure state.
    """

    get_owned_match(match_id, current_user, db)
    replay = get_match_replay(match_id, replay_id, db)
    if replay.upload_status != "uploaded" or not replay.storage_key:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Replay upload must be confirmed before inspection.")

    replay.processing_status = "processing"
    replay.processing_error = None
    replay.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(replay)

    try:
        # TemporaryDirectory cleans up when this block ends, including when an
        # exception occurs. The private MP4 should never remain on disk after the
        # request finishes.
        with TemporaryDirectory() as temporary_directory:
            video_path = f"{temporary_directory}/replay.mp4"
            storage.download_object_to_file(replay.storage_key, video_path)
            metadata = inspector.inspect(video_path)
    except VideoInspectionError as error:
        mark_inspection_failed(db, replay, error.public_message)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error.public_message) from error
    except Exception as error:
        mark_inspection_failed(db, replay, "Unable to access replay video for inspection.")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to access replay video for inspection.") from error

    replay.processing_status = "processed"
    replay.processing_error = None
    replay.metadata_inspected_at = datetime.now(timezone.utc)
    replay.video_duration_seconds = metadata.duration_seconds
    replay.video_width = metadata.width
    replay.video_height = metadata.height
    replay.video_fps = metadata.fps
    replay.video_codec = metadata.codec
    replay.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(replay)
    return ReplayInspectResponse(replay=replay)


def mark_inspection_failed(db: Session, replay: Replay, message: str) -> None:
    """Save a safe inspection failure so it remains visible after page reloads."""

    replay.processing_status = "failed"
    replay.processing_error = message[:255]
    replay.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(replay)


@router.post("/{replay_id}/frames/sample")
def sample_replay_frame(
    match_id: int,
    replay_id: int,
    payload: ReplayFrameSampleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: S3CompatibleStorageService = Depends(get_storage_service),
    extractor: FFmpegFrameExtractionService = Depends(get_frame_extraction_service),
) -> Response:
    """Extract one JPEG frame without exposing the MP4 or a local server path."""

    get_owned_match(match_id, current_user, db)
    replay = get_match_replay(match_id, replay_id, db)
    validate_frame_sampling_replay(replay)
    timestamp_seconds = validate_frame_timestamp(payload.timestamp_seconds, replay.video_duration_seconds)

    try:
        with TemporaryDirectory() as temporary_directory:
            video_path = Path(temporary_directory) / "replay.mp4"
            frame_path = Path(temporary_directory) / "frame.jpg"
            extract_replay_frame(replay, timestamp_seconds, video_path, frame_path, storage, extractor)
            frame_bytes = frame_path.read_bytes()
    except FrameExtractionError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error.public_message) from error
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to sample replay frame.") from error

    if not frame_bytes:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Frame extraction did not produce an image.")
    return Response(content=frame_bytes, media_type="image/jpeg")


@router.post("/{replay_id}/hud-detection", response_model=ReplayHudDetectionResponse)
def detect_replay_frame_hud(
    match_id: int,
    replay_id: int,
    payload: ReplayFrameSampleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: S3CompatibleStorageService = Depends(get_storage_service),
    extractor: FFmpegFrameExtractionService = Depends(get_frame_extraction_service),
    detector: GGSTHudDetectionService = Depends(get_hud_detection_service),
) -> ReplayHudDetectionResponse:
    """Extract one frame and measure whether the combat HUD is visible."""

    get_owned_match(match_id, current_user, db)
    replay = get_match_replay(match_id, replay_id, db)
    validate_frame_sampling_replay(replay)
    timestamp_seconds = validate_frame_timestamp(payload.timestamp_seconds, replay.video_duration_seconds)

    try:
        with TemporaryDirectory() as temporary_directory:
            video_path = Path(temporary_directory) / "replay.mp4"
            frame_path = Path(temporary_directory) / "frame.jpg"
            extract_replay_frame(replay, timestamp_seconds, video_path, frame_path, storage, extractor)
            detection = detector.detect(frame_path)
    except FrameExtractionError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error.public_message) from error
    except GGSTHudDetectionError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error.public_message) from error
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to detect replay HUD.") from error

    return ReplayHudDetectionResponse(
        timestamp_seconds=timestamp_seconds,
        classification=detection.classification,
        evidence=detection.evidence,
        measurements=detection.measurements,
    )


@router.post("/{replay_id}/hud-detections", response_model=ReplayHudDetectionBatchResponse)
def detect_replay_frame_huds(
    match_id: int,
    replay_id: int,
    payload: ReplayHudDetectionBatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: S3CompatibleStorageService = Depends(get_storage_service),
    extractor: FFmpegFrameExtractionService = Depends(get_frame_extraction_service),
    detector: GGSTHudDetectionService = Depends(get_hud_detection_service),
) -> ReplayHudDetectionBatchResponse:
    """Check several timestamps while downloading the private MP4 only once."""

    get_owned_match(match_id, current_user, db)
    replay = get_match_replay(match_id, replay_id, db)
    validate_frame_sampling_replay(replay)
    timestamps_seconds = [
        validate_frame_timestamp(timestamp_seconds, replay.video_duration_seconds)
        for timestamp_seconds in payload.timestamps_seconds
    ]

    samples: list[ReplayHudDetectionResponse] = []
    try:
        with TemporaryDirectory() as temporary_directory:
            video_path = Path(temporary_directory) / "replay.mp4"
            storage.download_object_to_file(replay.storage_key, video_path)
            for index, timestamp_seconds in enumerate(timestamps_seconds):
                frame_path = Path(temporary_directory) / f"frame-{index}.jpg"
                extractor.extract_jpeg_frame(video_path, timestamp_seconds, frame_path)
                detection = detector.detect(frame_path)
                samples.append(
                    ReplayHudDetectionResponse(
                        timestamp_seconds=timestamp_seconds,
                        classification=detection.classification,
                        evidence=detection.evidence,
                        measurements=detection.measurements,
                    )
                )
    except FrameExtractionError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error.public_message) from error
    except GGSTHudDetectionError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error.public_message) from error
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to detect replay HUD.") from error

    return ReplayHudDetectionBatchResponse(samples=samples)


def extract_replay_frame(
    replay: Replay,
    timestamp_seconds: float,
    video_path: Path,
    frame_path: Path,
    storage: S3CompatibleStorageService,
    extractor: FFmpegFrameExtractionService,
) -> None:
    """Combine the storage download and FFmpeg extraction steps."""

    storage.download_object_to_file(replay.storage_key, video_path)
    extractor.extract_jpeg_frame(video_path, timestamp_seconds, frame_path)


def validate_frame_sampling_replay(replay: Replay) -> None:
    """Check cheap prerequisites before downloading or running FFmpeg.

    Sampling requires both a confirmed upload and inspected duration. Performing
    these checks first avoids expensive work that cannot produce a valid result.
    """

    if replay.upload_status != "uploaded" or not replay.storage_key:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Replay upload must be confirmed before frame sampling.")
    if replay.processing_status != "processed" or replay.video_duration_seconds is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Replay video metadata must be inspected before frame sampling.")


def validate_frame_timestamp(timestamp_seconds: float, video_duration_seconds: float | None) -> float:
    """Reject timestamps at or beyond the inspected end of the video."""

    if video_duration_seconds is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Replay video duration is not available.")
    if timestamp_seconds >= video_duration_seconds:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Timestamp must be before the end of the video.",
        )
    return timestamp_seconds


@router.patch("/{replay_id}", response_model=ReplayRead)
def update_replay(match_id: int, replay_id: int, payload: ReplayUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Replay:
    get_owned_match(match_id, current_user, db)
    replay = get_match_replay(match_id, replay_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(replay, field, value)
    replay.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(replay)
    return replay


@router.delete("/{replay_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_replay(
    match_id: int,
    replay_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: S3CompatibleStorageService | None = Depends(get_optional_storage_service),
) -> None:
    """Delete the R2 video first, then delete its PostgreSQL record.

    This order is intentional. If R2 deletion fails, the row remains available
    for another attempt instead of leaving an untracked private video behind.
    """

    get_owned_match(match_id, current_user, db)
    replay = get_match_replay(match_id, replay_id, db)
    delete_storage_object_or_raise(replay.storage_key, storage)
    db.delete(replay)
    db.commit()


"""
Define the API routes for managing replay records and private video uploads.

These routes verify that users own the associated matches before allowing
access to their replays. They coordinate uploads to Cloudflare R2, confirm
uploaded files, and manage replay metadata stored in PostgreSQL.

They also handle video inspection, frame extraction, and HUD detection.
Video processing uses temporary local files that are cleaned up afterward.
"""