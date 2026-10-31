import math
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from app.services.frame_extraction import FFmpegFrameExtractionService, FrameExtractionError
from app.services.ggst_hud_detection import GGSTHudClassification, GGSTHudDetectionError, GGSTHudDetectionService
from app.services.replay_gameplay_windows import ReplayGameplayBoundary

BoundaryDirection = Literal["start", "end"]
BoundaryRefinementStatus = Literal["ok", "unknown", "failed"]
BoundaryRefinementStopReason = Literal[
    "tolerance_reached",
    "max_samples_reached",
    "no_distinct_timestamp",
]
BoundarySampleStatus = Literal["ok", "failed"]

BOUNDARY_REFINEMENT_ANALYZER_VERSION = "1.0.0"
DEFAULT_TARGET_TOLERANCE_SECONDS = 0.25
DEFAULT_MAX_REFINEMENT_SAMPLES = 8
DEFAULT_MIN_CONSECUTIVE_LIKELY_SAMPLES = 2
TIMESTAMP_PRECISION_DIGITS = 3
MIN_TIMESTAMP_STEP_SECONDS = 10 ** -TIMESTAMP_PRECISION_DIGITS


class ReplayGameplayBoundaryRefinementError(RuntimeError):
    def __init__(self, public_message: str) -> None:
        super().__init__(public_message)
        self.public_message = public_message


@dataclass(frozen=True)
class ReplayGameplayBoundaryRefinementConfig:
    target_tolerance_seconds: float = DEFAULT_TARGET_TOLERANCE_SECONDS
    max_samples: int = DEFAULT_MAX_REFINEMENT_SAMPLES
    min_consecutive_likely_samples: int = DEFAULT_MIN_CONSECUTIVE_LIKELY_SAMPLES


@dataclass(frozen=True)
class ReplayGameplayBoundarySample:
    timestamp_seconds: float
    status: BoundarySampleStatus
    classification: GGSTHudClassification | None
    error: str | None


@dataclass(frozen=True)
class ReplayGameplayBoundaryRefinementResult:
    analyzer_version: str
    direction: BoundaryDirection
    original_boundary: ReplayGameplayBoundary
    refined_boundary: ReplayGameplayBoundary
    status: BoundaryRefinementStatus
    stop_reason: BoundaryRefinementStopReason
    target_tolerance_seconds: float
    max_samples: int
    min_consecutive_likely_samples: int
    samples: tuple[ReplayGameplayBoundarySample, ...]
    unknown_samples: int
    failed_samples: int


class ReplayGameplayBoundaryRefiner:
    """Refine one sampled boundary without claiming unsampled precision."""

    def __init__(
        self,
        frame_extractor: FFmpegFrameExtractionService | None = None,
        hud_detector: GGSTHudDetectionService | None = None,
    ) -> None:
        self.frame_extractor = frame_extractor or FFmpegFrameExtractionService()
        self.hud_detector = hud_detector or GGSTHudDetectionService()

    def refine(
        self,
        video_path: str | Path,
        boundary: ReplayGameplayBoundary,
        direction: BoundaryDirection,
        config: ReplayGameplayBoundaryRefinementConfig | None = None,
    ) -> ReplayGameplayBoundaryRefinementResult:
        rules = config or ReplayGameplayBoundaryRefinementConfig()
        validate_refinement_request(boundary, direction, rules)

        samples: list[ReplayGameplayBoundarySample] = []
        sampled_timestamps: list[float] = []
        stop_reason: BoundaryRefinementStopReason = "tolerance_reached"
        refined_boundary = boundary
        conclusive_transition = False

        with TemporaryDirectory() as temporary_directory:
            while refined_boundary.latest_seconds - refined_boundary.earliest_seconds > rules.target_tolerance_seconds:
                if len(samples) >= rules.max_samples:
                    stop_reason = "max_samples_reached"
                    break

                timestamp_seconds = select_refinement_timestamp(
                    boundary.earliest_seconds,
                    boundary.latest_seconds,
                    sampled_timestamps,
                )
                if timestamp_seconds is None:
                    stop_reason = "no_distinct_timestamp"
                    break

                frame_path = Path(temporary_directory) / f"boundary-frame-{len(samples)}.jpg"
                try:
                    self.frame_extractor.extract_jpeg_frame(video_path, timestamp_seconds, frame_path)
                    detection = self.hud_detector.detect(frame_path)
                    sample = ReplayGameplayBoundarySample(
                        timestamp_seconds=timestamp_seconds,
                        status="ok",
                        classification=detection.classification,
                        error=None,
                    )
                except (FrameExtractionError, GGSTHudDetectionError) as error:
                    sample = ReplayGameplayBoundarySample(
                        timestamp_seconds=timestamp_seconds,
                        status="failed",
                        classification=None,
                        error=error.public_message,
                    )
                finally:
                    frame_path.unlink(missing_ok=True)

                samples.append(sample)
                sampled_timestamps.append(timestamp_seconds)
                refined_boundary, conclusive_transition = derive_refined_boundary(
                    boundary,
                    direction,
                    samples,
                    rules.min_consecutive_likely_samples,
                )

        status = refinement_status(refined_boundary, samples, rules, conclusive_transition)

        return ReplayGameplayBoundaryRefinementResult(
            analyzer_version=BOUNDARY_REFINEMENT_ANALYZER_VERSION,
            direction=direction,
            original_boundary=boundary,
            refined_boundary=refined_boundary,
            status=status,
            stop_reason=stop_reason,
            target_tolerance_seconds=rules.target_tolerance_seconds,
            max_samples=rules.max_samples,
            min_consecutive_likely_samples=rules.min_consecutive_likely_samples,
            samples=tuple(samples),
            unknown_samples=sum(1 for sample in samples if sample.classification == "unknown"),
            failed_samples=sum(1 for sample in samples if sample.status == "failed"),
        )


def select_refinement_timestamp(
    earliest_seconds: float,
    latest_seconds: float,
    sampled_timestamps: list[float],
) -> float | None:
    """Choose the earliest widest unsampled interval, then bisect it."""

    in_range_samples = [
        timestamp
        for timestamp in sampled_timestamps
        if earliest_seconds < timestamp < latest_seconds
    ]
    partition = sorted({earliest_seconds, latest_seconds, *in_range_samples})
    intervals = list(zip(partition, partition[1:]))
    intervals.sort(key=lambda interval: (-(interval[1] - interval[0]), interval[0]))

    for interval_start, interval_end in intervals:
        timestamp = round((interval_start + interval_end) / 2, TIMESTAMP_PRECISION_DIGITS)
        if interval_start < timestamp < interval_end and timestamp not in sampled_timestamps:
            return timestamp
    return None


def derive_refined_boundary(
    original_boundary: ReplayGameplayBoundary,
    direction: BoundaryDirection,
    samples: list[ReplayGameplayBoundarySample],
    min_consecutive_likely_samples: int,
) -> tuple[ReplayGameplayBoundary, bool]:
    ordered_samples = sorted(samples, key=lambda sample: sample.timestamp_seconds)
    if direction == "start":
        return derive_start_boundary(original_boundary, ordered_samples, min_consecutive_likely_samples)
    return derive_end_boundary(original_boundary, ordered_samples, min_consecutive_likely_samples)


def derive_start_boundary(
    original_boundary: ReplayGameplayBoundary,
    samples: list[ReplayGameplayBoundarySample],
    min_consecutive_likely_samples: int,
) -> tuple[ReplayGameplayBoundary, bool]:
    for index in range(len(samples) - min_consecutive_likely_samples + 1):
        likely_run = samples[index:index + min_consecutive_likely_samples]
        if all(is_likely_sample(sample) for sample in likely_run):
            previous_sample = samples[index - 1] if index > 0 else None
            earliest_seconds = (
                previous_sample.timestamp_seconds
                if previous_sample is not None
                else original_boundary.earliest_seconds
            )
            refined = ReplayGameplayBoundary(
                earliest_seconds=earliest_seconds,
                latest_seconds=likely_run[0].timestamp_seconds,
                kind=original_boundary.kind,
            )
            return refined, is_negative_sample(previous_sample)
    return original_boundary, False


def derive_end_boundary(
    original_boundary: ReplayGameplayBoundary,
    samples: list[ReplayGameplayBoundarySample],
    min_consecutive_likely_samples: int,
) -> tuple[ReplayGameplayBoundary, bool]:
    candidate: tuple[ReplayGameplayBoundary, bool] | None = None
    for index in range(len(samples) - min_consecutive_likely_samples):
        likely_run = samples[index:index + min_consecutive_likely_samples]
        following_sample = samples[index + min_consecutive_likely_samples]
        if all(is_likely_sample(sample) for sample in likely_run) and not is_likely_sample(following_sample):
            candidate = (
                ReplayGameplayBoundary(
                    earliest_seconds=likely_run[-1].timestamp_seconds,
                    latest_seconds=following_sample.timestamp_seconds,
                    kind=original_boundary.kind,
                ),
                is_negative_sample(following_sample),
            )
    return candidate or (original_boundary, False)


def is_likely_sample(sample: ReplayGameplayBoundarySample | None) -> bool:
    return sample is not None and sample.status == "ok" and sample.classification == "likely_gameplay_hud"


def is_negative_sample(sample: ReplayGameplayBoundarySample | None) -> bool:
    return sample is not None and sample.status == "ok" and sample.classification == "not_gameplay_hud"


def refinement_status(
    boundary: ReplayGameplayBoundary,
    samples: list[ReplayGameplayBoundarySample],
    config: ReplayGameplayBoundaryRefinementConfig,
    conclusive_transition: bool,
) -> BoundaryRefinementStatus:
    if boundary.latest_seconds - boundary.earliest_seconds <= config.target_tolerance_seconds and conclusive_transition:
        return "ok"
    if samples and all(sample.status == "failed" for sample in samples):
        return "failed"
    return "unknown"


def validate_refinement_request(
    boundary: ReplayGameplayBoundary,
    direction: BoundaryDirection,
    config: ReplayGameplayBoundaryRefinementConfig,
) -> None:
    if direction not in {"start", "end"}:
        raise ReplayGameplayBoundaryRefinementError("Boundary direction must be start or end.")

    for timestamp in (boundary.earliest_seconds, boundary.latest_seconds):
        if not isinstance(timestamp, (int, float)) or not math.isfinite(timestamp) or timestamp < 0:
            raise ReplayGameplayBoundaryRefinementError("Boundary timestamps must be finite numbers greater than or equal to 0.")
    if boundary.latest_seconds < boundary.earliest_seconds:
        raise ReplayGameplayBoundaryRefinementError("Boundary latest timestamp must not be before its earliest timestamp.")

    tolerance = config.target_tolerance_seconds
    if not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or tolerance < MIN_TIMESTAMP_STEP_SECONDS:
        raise ReplayGameplayBoundaryRefinementError("Target tolerance must be at least 0.001 seconds.")
    if type(config.max_samples) is not int or config.max_samples <= 0:
        raise ReplayGameplayBoundaryRefinementError("Maximum samples must be a positive integer.")
    if type(config.min_consecutive_likely_samples) is not int or config.min_consecutive_likely_samples < 2:
        raise ReplayGameplayBoundaryRefinementError("Minimum consecutive likely samples must be an integer of at least 2.")
