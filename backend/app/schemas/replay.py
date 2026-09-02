import math
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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
    original_filename: str | None = Field(default=None, max_length=255)
    content_type: Literal["video/mp4"]
    size_bytes: int = Field(gt=0)

    _clean_original_filename = field_validator("original_filename")(clean_optional_filename)
    model_config = ConfigDict(extra="forbid")


class ReplayRead(BaseModel):
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
    timestamp_seconds: float = Field(ge=0)

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")


class ReplayHudDetectionResponse(BaseModel):
    timestamp_seconds: float
    classification: GGSTHudClassification
    evidence: dict[str, bool]
    measurements: dict[str, float]


class ReplayHudDetectionBatchRequest(BaseModel):
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
