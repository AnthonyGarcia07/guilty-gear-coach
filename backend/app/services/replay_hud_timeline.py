import math
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from app.services.frame_extraction import FFmpegFrameExtractionService, FrameExtractionError
from app.services.ggst_hud_detection import GGSTHudClassification, GGSTHudDetectionError, GGSTHudDetectionService

TimelineSampleStatus = Literal["ok", "failed"]

DEFAULT_MAX_TIMELINE_SAMPLES = 120
TIMESTAMP_PRECISION_DIGITS = 3


class ReplayHudTimelineError(RuntimeError):
    def __init__(self, public_message: str) -> None:
        super().__init__(public_message)
        self.public_message = public_message


@dataclass(frozen=True)
class ReplayHudTimelineSample:
    timestamp_seconds: float
    status: TimelineSampleStatus
    classification: GGSTHudClassification | None
    evidence: dict[str, bool] | None
    measurements: dict[str, float] | None
    error: str | None


@dataclass(frozen=True)
class ReplayHudTimeline:
    duration_seconds: float
    interval_seconds: float
    start_offset_seconds: float
    samples: list[ReplayHudTimelineSample]


class ReplayHudTimelineScanner:
    def __init__(
        self,
        frame_extractor: FFmpegFrameExtractionService | None = None,
        hud_detector: GGSTHudDetectionService | None = None,
    ) -> None:
        self.frame_extractor = frame_extractor or FFmpegFrameExtractionService()
        self.hud_detector = hud_detector or GGSTHudDetectionService()

    def scan(
        self,
        video_path: str | Path,
        duration_seconds: float,
        interval_seconds: float,
        start_offset_seconds: float = 0.0,
        max_samples: int = DEFAULT_MAX_TIMELINE_SAMPLES,
    ) -> ReplayHudTimeline:
        timestamps_seconds = generate_replay_sample_timestamps(
            duration_seconds=duration_seconds,
            interval_seconds=interval_seconds,
            start_offset_seconds=start_offset_seconds,
            max_samples=max_samples,
        )
        samples: list[ReplayHudTimelineSample] = []

        with TemporaryDirectory() as temporary_directory:
            for index, timestamp_seconds in enumerate(timestamps_seconds):
                frame_path = Path(temporary_directory) / f"frame-{index}.jpg"
                try:
                    self.frame_extractor.extract_jpeg_frame(video_path, timestamp_seconds, frame_path)
                    detection = self.hud_detector.detect(frame_path)
                except FrameExtractionError as error:
                    samples.append(failed_sample(timestamp_seconds, error.public_message))
                    continue
                except GGSTHudDetectionError as error:
                    samples.append(failed_sample(timestamp_seconds, error.public_message))
                    continue
                finally:
                    frame_path.unlink(missing_ok=True)

                samples.append(
                    ReplayHudTimelineSample(
                        timestamp_seconds=timestamp_seconds,
                        status="ok",
                        classification=detection.classification,
                        evidence=detection.evidence,
                        measurements=detection.measurements,
                        error=None,
                    )
                )

        return ReplayHudTimeline(
            duration_seconds=normalize_positive_float(duration_seconds, "Duration"),
            interval_seconds=normalize_positive_float(interval_seconds, "Interval"),
            start_offset_seconds=normalize_non_negative_float(start_offset_seconds, "Start offset"),
            samples=samples,
        )


def generate_replay_sample_timestamps(
    duration_seconds: float,
    interval_seconds: float,
    start_offset_seconds: float = 0.0,
    max_samples: int = DEFAULT_MAX_TIMELINE_SAMPLES,
) -> list[float]:
    duration = normalize_positive_float(duration_seconds, "Duration")
    interval = normalize_positive_float(interval_seconds, "Interval")
    start_offset = normalize_non_negative_float(start_offset_seconds, "Start offset")
    validate_positive_integer(max_samples, "Maximum samples")

    if start_offset >= duration:
        raise ReplayHudTimelineError("Start offset must be before the end of the video.")

    timestamps: list[float] = []
    next_timestamp = start_offset
    while next_timestamp < duration:
        timestamp = round(next_timestamp, TIMESTAMP_PRECISION_DIGITS)
        if timestamp >= duration:
            break
        if timestamps and timestamp <= timestamps[-1]:
            raise ReplayHudTimelineError("Interval is too small for millisecond timestamp precision.")
        timestamps.append(timestamp)
        if len(timestamps) > max_samples:
            raise ReplayHudTimelineError("Requested timeline would exceed the maximum sample count.")
        next_timestamp = start_offset + len(timestamps) * interval

    return timestamps


def failed_sample(timestamp_seconds: float, public_message: str) -> ReplayHudTimelineSample:
    return ReplayHudTimelineSample(
        timestamp_seconds=timestamp_seconds,
        status="failed",
        classification=None,
        evidence=None,
        measurements=None,
        error=public_message,
    )


def normalize_positive_float(value: float, label: str) -> float:
    try:
        normalized = float(value)
    except (TypeError, ValueError) as error:
        raise ReplayHudTimelineError(f"{label} must be a finite number greater than 0.") from error
    if not math.isfinite(normalized) or normalized <= 0:
        raise ReplayHudTimelineError(f"{label} must be a finite number greater than 0.")
    return normalized


def normalize_non_negative_float(value: float, label: str) -> float:
    try:
        normalized = float(value)
    except (TypeError, ValueError) as error:
        raise ReplayHudTimelineError(f"{label} must be a finite number greater than or equal to 0.") from error
    if not math.isfinite(normalized) or normalized < 0:
        raise ReplayHudTimelineError(f"{label} must be a finite number greater than or equal to 0.")
    return normalized


def validate_positive_integer(value: int, label: str) -> None:
    if type(value) is not int or value <= 0:
        raise ReplayHudTimelineError(f"{label} must be a positive integer.")
