"""Define and validate the replay API's request and response shapes.

SQLAlchemy models describe database rows; these Pydantic models describe JSON
sent across the HTTP API. Request models contain only fields the browser is
allowed to choose. Response models can also contain server-owned fields such as
upload status and inspected video details.

This separation is a security boundary. For example, the browser may describe
the file it wants to upload, but it cannot declare that the upload succeeded or
invent trusted ffprobe results.
"""

import math
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ``Literal`` creates a closed set of accepted strings. These values match the
# model's database constraints and the frontend TypeScript unions. If one list
# changes, the other layers and their tests must be updated too.
ReplaySourceType = Literal["replay_file", "video", "external_reference"]
ReplayUploadStatus = Literal["metadata_only", "pending_upload", "uploaded"]
ReplayProcessingStatus = Literal["not_processed", "processing", "processed", "failed"]
GGSTHudClassification = Literal["likely_gameplay_hud", "not_gameplay_hud", "unknown"]


def clean_optional_filename(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class ReplayCreate(BaseModel):
    source_type: ReplaySourceType
    original_filename: str | None = Field(default=None, max_length=255)

    _clean_original_filename = field_validator("original_filename")(clean_optional_filename)
    model_config = ConfigDict(extra="forbid")


class ReplayUpdate(BaseModel):
    source_type: ReplaySourceType | None = None
    original_filename: str | None = Field(default=None, max_length=255)

    @model_validator(mode="before")
    @classmethod
    def reject_null_source_type(cls, data: object) -> object:
        if isinstance(data, dict) and "source_type" in data and data["source_type"] is None:
            raise ValueError("Source type cannot be null.")
        return data

    _clean_original_filename = field_validator("original_filename")(clean_optional_filename)
    model_config = ConfigDict(extra="forbid")


class ReplayUploadInit(BaseModel):
    """Validate the browser's description of an MP4 before upload begins.

    These values are still untrusted claims. The backend checks the real object
    metadata from R2 during upload confirmation.
    """

    original_filename: str | None = Field(default=None, max_length=255)
    content_type: Literal["video/mp4"]
    size_bytes: int = Field(gt=0)

    _clean_original_filename = field_validator("original_filename")(clean_optional_filename)
    model_config = ConfigDict(extra="forbid")


class ReplayRead(BaseModel):
    """Describe a replay returned to the browser.

    ``from_attributes`` below lets Pydantic read these fields directly from a
    SQLAlchemy ``Replay`` object instead of requiring a manually built dict.
    """

    id: int
    match_id: int
    source_type: ReplaySourceType
    original_filename: str | None = None
    storage_key: str | None = None
    upload_status: ReplayUploadStatus
    content_type: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    uploaded_at: datetime | None = None
    processing_status: ReplayProcessingStatus
    processing_error: str | None = None
    metadata_inspected_at: datetime | None = None
    video_duration_seconds: float | None = Field(default=None, ge=0)
    video_width: int | None = Field(default=None, gt=0)
    video_height: int | None = Field(default=None, gt=0)
    video_fps: float | None = Field(default=None, gt=0)
    video_codec: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReplayUploadInitResponse(BaseModel):
    """Return the pending replay plus a temporary URL for uploading its MP4."""

    replay: ReplayRead
    upload_url: str
    storage_key: str
    expires_in_seconds: int


class ReplayUploadConfirmResponse(BaseModel):
    replay: ReplayRead


class ReplayDownloadUrlResponse(BaseModel):
    download_url: str
    expires_in_seconds: int


class ReplayInspectResponse(BaseModel):
    replay: ReplayRead


class ReplayFrameSampleRequest(BaseModel):
    """Request one video frame at a timestamp measured in seconds.

    This schema rejects negative, infinite, and NaN values. The route performs
    the separate check that the timestamp is before this video's end.
    """

    timestamp_seconds: float = Field(ge=0)

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")


class ReplayHudDetectionResponse(BaseModel):
    timestamp_seconds: float
    classification: GGSTHudClassification
    evidence: dict[str, bool]
    measurements: dict[str, float]


class ReplayHudDetectionBatchRequest(BaseModel):
    """Validate a small batch of timestamps for HUD detection.

    The limit keeps one HTTP request from starting unbounded FFmpeg work. The
    validator also rejects duplicate or invalid timestamps before any video is
    downloaded or processed.
    """

    timestamps_seconds: list[float] = Field(min_length=1, max_length=10)

    @field_validator("timestamps_seconds")
    @classmethod
    def reject_duplicate_timestamps(cls, value: list[float]) -> list[float]:
        for timestamp_seconds in value:
            if not math.isfinite(timestamp_seconds) or timestamp_seconds < 0:
                raise ValueError("Timestamps must be finite numbers greater than or equal to 0.")
        if len(value) != len(set(value)):
            raise ValueError("Duplicate timestamps are not allowed.")
        return value

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")


class ReplayHudDetectionBatchResponse(BaseModel):
    samples: list[ReplayHudDetectionResponse]


"""
"I use Pydantic schemas to define and validate the JSON exchanged between my React frontend and FastAPI backend.

The schemas separate user-controlled fields from server-controlled fields.
For example, users can provide an MP4 filename and file size when initiating an upload, 
but they cannot directly set its upload status or processing results.
The backend verifies the upload and populates those fields itself."
"""
