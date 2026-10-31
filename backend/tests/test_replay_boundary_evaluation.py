import json
import subprocess

import pytest

from app.services.replay_boundary_evaluation import (
    ReplayBoundaryEvaluationCase,
    ReplayBoundaryEvaluationDataset,
    ReplayBoundaryEvaluationError,
    evaluate_boundary_dataset,
    interval_error_seconds,
    load_boundary_evaluation_dataset,
    read_ffmpeg_version,
    resolve_clip_path,
)
from app.services.replay_gameplay_boundary_refinement import (
    BOUNDARY_REFINEMENT_ANALYZER_VERSION,
    ReplayGameplayBoundaryRefinementConfig,
    ReplayGameplayBoundaryRefinementResult,
    ReplayGameplayBoundarySample,
)
from app.services.replay_gameplay_windows import ReplayGameplayBoundary


def boundary(earliest_seconds: float, latest_seconds: float) -> ReplayGameplayBoundary:
    return ReplayGameplayBoundary(earliest_seconds, latest_seconds, "between_samples")


def manifest(case_overrides: dict | None = None) -> dict:
    case = {
        "case_id": "match-one-start",
        "clip_filename": "match-one.mp4",
        "direction": "start",
        "coarse_boundary": {"earliest_seconds": 8.0, "latest_seconds": 12.0},
        "expected_boundary": {"earliest_seconds": 9.0, "latest_seconds": 9.5},
        "expected_status": "ok",
        "source_resolution": "1920x1080",
        "source_frame_rate_fps": 60.0,
        "game_patch": "unknown",
        "label_reviewed_by": "project owner",
        "label_reviewed_on": "2026-10-31",
        "notes": "Duel transition is visually ambiguous.",
    }
    case.update(case_overrides or {})
    return {
        "dataset_version": "1.0.0",
        "analyzer_version": BOUNDARY_REFINEMENT_ANALYZER_VERSION,
        "config": {
            "target_tolerance_seconds": 0.5,
            "max_samples": 6,
            "min_consecutive_likely_samples": 2,
        },
        "cases": [case],
    }


class FakeRefiner:
    def __init__(self, results: list[ReplayGameplayBoundaryRefinementResult]) -> None:
        self.results = iter(results)
        self.calls = []

    def refine(self, video_path, coarse_boundary, direction, config):
        self.calls.append((video_path, coarse_boundary, direction, config))
        return next(self.results)


def result(
    original: ReplayGameplayBoundary,
    refined: ReplayGameplayBoundary,
    samples: tuple[ReplayGameplayBoundarySample, ...],
) -> ReplayGameplayBoundaryRefinementResult:
    return ReplayGameplayBoundaryRefinementResult(
        analyzer_version=BOUNDARY_REFINEMENT_ANALYZER_VERSION,
        direction="start",
        original_boundary=original,
        refined_boundary=refined,
        status="ok",
        stop_reason="tolerance_reached",
        target_tolerance_seconds=0.5,
        max_samples=6,
        min_consecutive_likely_samples=2,
        samples=samples,
        unknown_samples=sum(sample.classification == "unknown" for sample in samples),
        failed_samples=sum(sample.status == "failed" for sample in samples),
    )


def test_loads_versioned_manifest_with_explicit_units(tmp_path):
    manifest_path = tmp_path / "boundaries.json"
    manifest_path.write_text(json.dumps(manifest()), encoding="utf-8")

    dataset = load_boundary_evaluation_dataset(manifest_path)

    assert dataset.dataset_version == "1.0.0"
    assert dataset.analyzer_version == BOUNDARY_REFINEMENT_ANALYZER_VERSION
    assert dataset.config.target_tolerance_seconds == 0.5
    assert dataset.config.max_samples == 6
    assert dataset.config.min_consecutive_likely_samples == 2
    assert dataset.cases[0].coarse_boundary == boundary(8.0, 12.0)
    assert dataset.cases[0].expected_boundary == boundary(9.0, 9.5)


@pytest.mark.parametrize(
    "invalid_manifest",
    [
        {},
        {**manifest(), "cases": []},
        {**manifest(), "config": {**manifest()["config"], "min_consecutive_likely_samples": 1}},
        {**manifest(), "cases": [manifest()["cases"][0], manifest()["cases"][0]]},
        manifest({"direction": "middle"}),
        manifest({"expected_status": "maybe"}),
        manifest({"coarse_boundary": {"earliest_seconds": 12.0, "latest_seconds": 8.0}}),
        manifest({"expected_boundary": {"earliest_seconds": 7.0, "latest_seconds": 9.0}}),
        manifest({"source_frame_rate_fps": "sixty"}),
        manifest({"source_frame_rate_fps": 0}),
    ],
)
def test_rejects_invalid_or_ambiguous_manifest_contract(tmp_path, invalid_manifest):
    manifest_path = tmp_path / "invalid.json"
    manifest_path.write_text(json.dumps(invalid_manifest), encoding="utf-8")

    with pytest.raises(ReplayBoundaryEvaluationError):
        load_boundary_evaluation_dataset(manifest_path)


def test_interval_error_is_zero_for_overlap_and_distance_for_disjoint_ranges():
    assert interval_error_seconds(boundary(8.0, 10.0), boundary(9.0, 9.5)) == 0.0
    assert interval_error_seconds(boundary(4.0, 6.0), boundary(7.0, 8.0)) == 2.0
    assert interval_error_seconds(boundary(9.0, 10.0), boundary(7.0, 8.0)) == 1.5


def test_evaluation_reports_accuracy_ambiguity_failures_and_sampling_cost(tmp_path):
    clip_path = tmp_path / "match-one.mp4"
    clip_path.write_bytes(b"permitted fixture")
    case = ReplayBoundaryEvaluationCase(
        case_id="match-one-start",
        clip_filename=clip_path.name,
        direction="start",
        coarse_boundary=boundary(4.0, 8.0),
        expected_boundary=boundary(5.0, 5.5),
        expected_status="ok",
        source_resolution="1920x1080",
        source_frame_rate_fps=60.0,
        game_patch="unknown",
        label_reviewed_by="project owner",
        label_reviewed_on="2026-10-31",
        notes=None,
    )
    dataset = ReplayBoundaryEvaluationDataset(
        dataset_version="1.0.0",
        analyzer_version=BOUNDARY_REFINEMENT_ANALYZER_VERSION,
        config=ReplayGameplayBoundaryRefinementConfig(0.5, 6),
        cases=(case,),
    )
    samples = (
        ReplayGameplayBoundarySample(6.0, "ok", "unknown", None),
        ReplayGameplayBoundarySample(5.0, "ok", "not_gameplay_hud", None),
        ReplayGameplayBoundarySample(5.5, "failed", None, "Frame extraction failed."),
    )
    fake_refiner = FakeRefiner([result(case.coarse_boundary, boundary(5.0, 5.5), samples)])

    report = evaluate_boundary_dataset(dataset, tmp_path, fake_refiner, ffmpeg_version="ffmpeg test")

    assert report.ffmpeg_version == "ffmpeg test"
    assert report.mean_coarse_error_seconds == 0.5
    assert report.mean_refined_error_seconds == 0.0
    assert report.max_refined_error_seconds == 0.0
    assert report.unknown_rate == pytest.approx(1 / 3)
    assert report.failure_rate == pytest.approx(1 / 3)
    assert report.mean_samples_per_boundary == 3.0
    assert report.cases[0].coarse_width_seconds == 4.0
    assert report.cases[0].refined_width_seconds == 0.5
    assert report.cases[0].status_matches_expected is True
    assert fake_refiner.calls[0][0] == clip_path


def test_clip_path_must_be_relative_present_and_inside_media_root(tmp_path):
    (tmp_path / "clip.mp4").write_bytes(b"fixture")

    assert resolve_clip_path(tmp_path, "clip.mp4") == tmp_path / "clip.mp4"
    with pytest.raises(ReplayBoundaryEvaluationError):
        resolve_clip_path(tmp_path, "../clip.mp4")
    with pytest.raises(ReplayBoundaryEvaluationError):
        resolve_clip_path(tmp_path, "missing.mp4")


def test_reads_ffmpeg_version_with_bounded_safe_subprocess(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout="ffmpeg version 7.1 test\nmore")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert read_ffmpeg_version() == "ffmpeg version 7.1 test"
    assert calls[0][0] == ["ffmpeg", "-version"]
    assert calls[0][1]["timeout"] == 5
    assert "shell" not in calls[0][1]


def test_missing_ffmpeg_version_is_reported_without_raw_error(monkeypatch):
    def fake_run(command, **kwargs):
        raise FileNotFoundError("private host detail")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert read_ffmpeg_version() == "unavailable"
