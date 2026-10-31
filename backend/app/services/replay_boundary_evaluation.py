import json
import math
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from app.services.replay_gameplay_boundary_refinement import (
    BOUNDARY_REFINEMENT_ANALYZER_VERSION,
    MIN_TIMESTAMP_STEP_SECONDS,
    BoundaryDirection,
    ReplayGameplayBoundaryRefinementConfig,
    ReplayGameplayBoundaryRefiner,
)
from app.services.replay_gameplay_windows import ReplayGameplayBoundary


class ReplayBoundaryEvaluationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReplayBoundaryEvaluationCase:
    case_id: str
    clip_filename: str
    direction: BoundaryDirection
    coarse_boundary: ReplayGameplayBoundary
    expected_boundary: ReplayGameplayBoundary
    expected_status: Literal["ok", "unknown", "failed"]
    source_resolution: str
    source_frame_rate_fps: float
    game_patch: str | None
    label_reviewed_by: str
    label_reviewed_on: str
    notes: str | None


@dataclass(frozen=True)
class ReplayBoundaryEvaluationDataset:
    dataset_version: str
    analyzer_version: str
    config: ReplayGameplayBoundaryRefinementConfig
    cases: tuple[ReplayBoundaryEvaluationCase, ...]


@dataclass(frozen=True)
class ReplayBoundaryCaseMetrics:
    case_id: str
    status: str
    status_matches_expected: bool
    stop_reason: str
    coarse_error_seconds: float
    refined_error_seconds: float
    coarse_width_seconds: float
    refined_width_seconds: float
    samples: int
    unknown_samples: int
    failed_samples: int
    elapsed_seconds: float


@dataclass(frozen=True)
class ReplayBoundaryEvaluationReport:
    dataset_version: str
    analyzer_version: str
    ffmpeg_version: str
    target_tolerance_seconds: float
    max_samples_per_boundary: int
    min_consecutive_likely_samples: int
    cases: tuple[ReplayBoundaryCaseMetrics, ...]
    mean_coarse_error_seconds: float
    mean_refined_error_seconds: float
    max_refined_error_seconds: float
    unknown_rate: float
    failure_rate: float
    mean_samples_per_boundary: float
    total_elapsed_seconds: float


def load_boundary_evaluation_dataset(manifest_path: str | Path) -> ReplayBoundaryEvaluationDataset:
    path = Path(manifest_path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReplayBoundaryEvaluationError("Boundary evaluation manifest could not be read.") from error

    if not isinstance(raw, dict):
        raise ReplayBoundaryEvaluationError("Boundary evaluation manifest must contain a JSON object.")

    dataset_version = required_string(raw, "dataset_version")
    analyzer_version = required_string(raw, "analyzer_version")
    raw_config = required_mapping(raw, "config")
    config = ReplayGameplayBoundaryRefinementConfig(
        target_tolerance_seconds=required_number(raw_config, "target_tolerance_seconds"),
        max_samples=required_integer(raw_config, "max_samples"),
        min_consecutive_likely_samples=required_integer(raw_config, "min_consecutive_likely_samples"),
    )
    if (
        config.target_tolerance_seconds < MIN_TIMESTAMP_STEP_SECONDS
        or config.max_samples <= 0
        or config.min_consecutive_likely_samples < 2
    ):
        raise ReplayBoundaryEvaluationError("Boundary evaluation configuration must use positive bounded values.")

    raw_cases = raw.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ReplayBoundaryEvaluationError("Boundary evaluation manifest must contain at least one case.")

    cases = tuple(parse_case(raw_case) for raw_case in raw_cases)
    case_ids = [case.case_id for case in cases]
    if len(set(case_ids)) != len(case_ids):
        raise ReplayBoundaryEvaluationError("Boundary evaluation case identifiers must be unique.")

    return ReplayBoundaryEvaluationDataset(dataset_version, analyzer_version, config, cases)


def evaluate_boundary_dataset(
    dataset: ReplayBoundaryEvaluationDataset,
    media_root: str | Path,
    refiner: ReplayGameplayBoundaryRefiner | None = None,
    ffmpeg_version: str | None = None,
) -> ReplayBoundaryEvaluationReport:
    if dataset.analyzer_version != BOUNDARY_REFINEMENT_ANALYZER_VERSION:
        raise ReplayBoundaryEvaluationError("Evaluation dataset analyzer version does not match the current analyzer.")
    boundary_refiner = refiner or ReplayGameplayBoundaryRefiner()
    root = Path(media_root)
    case_metrics: list[ReplayBoundaryCaseMetrics] = []
    total_samples = 0
    total_unknown = 0
    total_failed = 0
    total_elapsed_seconds = 0.0

    for case in dataset.cases:
        clip_path = resolve_clip_path(root, case.clip_filename)
        started_at = time.perf_counter()
        result = boundary_refiner.refine(
            clip_path,
            case.coarse_boundary,
            case.direction,
            dataset.config,
        )
        if result.analyzer_version != dataset.analyzer_version:
            raise ReplayBoundaryEvaluationError("Boundary refinement result used an unexpected analyzer version.")
        elapsed_seconds = time.perf_counter() - started_at
        metrics = ReplayBoundaryCaseMetrics(
            case_id=case.case_id,
            status=result.status,
            status_matches_expected=result.status == case.expected_status,
            stop_reason=result.stop_reason,
            coarse_error_seconds=interval_error_seconds(case.coarse_boundary, case.expected_boundary),
            refined_error_seconds=interval_error_seconds(result.refined_boundary, case.expected_boundary),
            coarse_width_seconds=boundary_width_seconds(case.coarse_boundary),
            refined_width_seconds=boundary_width_seconds(result.refined_boundary),
            samples=len(result.samples),
            unknown_samples=result.unknown_samples,
            failed_samples=result.failed_samples,
            elapsed_seconds=elapsed_seconds,
        )
        case_metrics.append(metrics)
        total_samples += metrics.samples
        total_unknown += metrics.unknown_samples
        total_failed += metrics.failed_samples
        total_elapsed_seconds += elapsed_seconds

    case_count = len(case_metrics)
    return ReplayBoundaryEvaluationReport(
        dataset_version=dataset.dataset_version,
        analyzer_version=dataset.analyzer_version,
        ffmpeg_version=ffmpeg_version or read_ffmpeg_version(),
        target_tolerance_seconds=dataset.config.target_tolerance_seconds,
        max_samples_per_boundary=dataset.config.max_samples,
        min_consecutive_likely_samples=dataset.config.min_consecutive_likely_samples,
        cases=tuple(case_metrics),
        mean_coarse_error_seconds=mean(metric.coarse_error_seconds for metric in case_metrics),
        mean_refined_error_seconds=mean(metric.refined_error_seconds for metric in case_metrics),
        max_refined_error_seconds=max(metric.refined_error_seconds for metric in case_metrics),
        unknown_rate=total_unknown / total_samples if total_samples else 0.0,
        failure_rate=total_failed / total_samples if total_samples else 0.0,
        mean_samples_per_boundary=total_samples / case_count,
        total_elapsed_seconds=total_elapsed_seconds,
    )


def evaluation_report_as_dict(report: ReplayBoundaryEvaluationReport) -> dict[str, Any]:
    return asdict(report)


def interval_error_seconds(actual: ReplayGameplayBoundary, expected: ReplayGameplayBoundary) -> float:
    """Measure the predicted midpoint's distance from the reviewed truth range."""

    actual_midpoint = (actual.earliest_seconds + actual.latest_seconds) / 2
    if actual_midpoint < expected.earliest_seconds:
        return expected.earliest_seconds - actual_midpoint
    if actual_midpoint > expected.latest_seconds:
        return actual_midpoint - expected.latest_seconds
    return 0.0


def boundary_width_seconds(boundary: ReplayGameplayBoundary) -> float:
    return boundary.latest_seconds - boundary.earliest_seconds


def resolve_clip_path(media_root: Path, clip_filename: str) -> Path:
    if not clip_filename or Path(clip_filename).is_absolute() or ".." in Path(clip_filename).parts:
        raise ReplayBoundaryEvaluationError("Evaluation clip filenames must be relative paths inside the media root.")
    clip_path = media_root / clip_filename
    if not clip_path.is_file():
        raise ReplayBoundaryEvaluationError(f"Evaluation clip is missing for identifier: {clip_filename}")
    return clip_path


def read_ffmpeg_version(ffmpeg_path: str = "ffmpeg") -> str:
    try:
        completed = subprocess.run(
            [ffmpeg_path, "-version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return "unavailable"
    first_line = completed.stdout.splitlines()[0] if completed.stdout else ""
    return first_line.strip() or "unavailable"


def parse_case(raw_case: object) -> ReplayBoundaryEvaluationCase:
    if not isinstance(raw_case, dict):
        raise ReplayBoundaryEvaluationError("Each boundary evaluation case must be a JSON object.")
    direction = required_string(raw_case, "direction")
    if direction not in {"start", "end"}:
        raise ReplayBoundaryEvaluationError("Evaluation boundary direction must be start or end.")
    expected_status = required_string(raw_case, "expected_status")
    if expected_status not in {"ok", "unknown", "failed"}:
        raise ReplayBoundaryEvaluationError("Evaluation expected status must be ok, unknown, or failed.")

    game_patch = raw_case.get("game_patch")
    notes = raw_case.get("notes")
    if game_patch is not None and not isinstance(game_patch, str):
        raise ReplayBoundaryEvaluationError("Evaluation game patch must be a string or null.")
    if notes is not None and not isinstance(notes, str):
        raise ReplayBoundaryEvaluationError("Evaluation notes must be a string or null.")

    coarse_boundary = parse_boundary(required_mapping(raw_case, "coarse_boundary"))
    expected_boundary = parse_boundary(required_mapping(raw_case, "expected_boundary"))
    if (
        expected_boundary.earliest_seconds < coarse_boundary.earliest_seconds
        or expected_boundary.latest_seconds > coarse_boundary.latest_seconds
    ):
        raise ReplayBoundaryEvaluationError("Expected boundary must remain inside its validated coarse boundary.")

    source_frame_rate_fps = required_number(raw_case, "source_frame_rate_fps")
    if source_frame_rate_fps <= 0:
        raise ReplayBoundaryEvaluationError("Evaluation source frame rate must be greater than 0.")

    return ReplayBoundaryEvaluationCase(
        case_id=required_string(raw_case, "case_id"),
        clip_filename=required_string(raw_case, "clip_filename"),
        direction=direction,
        coarse_boundary=coarse_boundary,
        expected_boundary=expected_boundary,
        expected_status=expected_status,
        source_resolution=required_string(raw_case, "source_resolution"),
        source_frame_rate_fps=source_frame_rate_fps,
        game_patch=game_patch,
        label_reviewed_by=required_string(raw_case, "label_reviewed_by"),
        label_reviewed_on=required_string(raw_case, "label_reviewed_on"),
        notes=notes,
    )


def parse_boundary(raw: dict[str, object]) -> ReplayGameplayBoundary:
    earliest = required_number(raw, "earliest_seconds")
    latest = required_number(raw, "latest_seconds")
    if earliest < 0 or latest < earliest:
        raise ReplayBoundaryEvaluationError("Evaluation boundaries must be ordered non-negative ranges.")
    return ReplayGameplayBoundary(earliest, latest, "between_samples")


def required_mapping(raw: dict[str, object], key: str) -> dict[str, object]:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise ReplayBoundaryEvaluationError(f"Evaluation field '{key}' must be an object.")
    return value


def required_string(raw: dict[str, object], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ReplayBoundaryEvaluationError(f"Evaluation field '{key}' must be a non-empty string.")
    return value


def required_number(raw: dict[str, object], key: str) -> float:
    value = raw.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ReplayBoundaryEvaluationError(f"Evaluation field '{key}' must be a finite number.")
    return float(value)


def required_integer(raw: dict[str, object], key: str) -> int:
    value = raw.get(key)
    if type(value) is not int:
        raise ReplayBoundaryEvaluationError(f"Evaluation field '{key}' must be an integer.")
    return value


def mean(values) -> float:
    collected = list(values)
    return sum(collected) / len(collected)
