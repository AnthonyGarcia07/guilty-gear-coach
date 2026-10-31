from pathlib import Path

import pytest

from app.services.frame_extraction import FrameExtractionError
from app.services.ggst_hud_detection import GGSTHudDetectionResult
from app.services.replay_gameplay_boundary_refinement import (
    BOUNDARY_REFINEMENT_ANALYZER_VERSION,
    ReplayGameplayBoundaryRefinementConfig,
    ReplayGameplayBoundaryRefinementError,
    ReplayGameplayBoundaryRefiner,
    ReplayGameplayBoundarySample,
    derive_refined_boundary,
    select_refinement_timestamp,
)
from app.services.replay_gameplay_windows import ReplayGameplayBoundary


class FakeFrameExtractor:
    def __init__(self, failed_timestamps: set[float] | None = None) -> None:
        self.failed_timestamps = failed_timestamps or set()
        self.calls: list[dict[str, object]] = []

    def extract_jpeg_frame(self, video_path, timestamp_seconds, output_path) -> None:
        self.calls.append({
            "video_path": Path(video_path),
            "timestamp_seconds": timestamp_seconds,
            "output_path": Path(output_path),
        })
        if timestamp_seconds in self.failed_timestamps:
            raise FrameExtractionError("Frame extraction failed.")
        Path(output_path).write_bytes(b"fake-jpeg")


class SequencedHudDetector:
    def __init__(self, classifications: list[str]) -> None:
        self.classifications = iter(classifications)
        self.calls: list[Path] = []

    def detect(self, image_path):
        self.calls.append(Path(image_path))
        classification = next(self.classifications)
        return GGSTHudDetectionResult(classification, {}, {})


def boundary(earliest_seconds: float = 0.0, latest_seconds: float = 8.0) -> ReplayGameplayBoundary:
    return ReplayGameplayBoundary(earliest_seconds, latest_seconds, "between_samples")


def test_selects_midpoint_then_splits_earliest_widest_interval():
    assert select_refinement_timestamp(0.0, 8.0, []) == 4.0
    assert select_refinement_timestamp(0.0, 8.0, [4.0]) == 2.0
    assert select_refinement_timestamp(0.0, 8.0, [2.0, 4.0]) == 6.0


def test_returns_none_when_millisecond_precision_has_no_interior_timestamp():
    assert select_refinement_timestamp(1.0, 1.001, []) is None


def test_ignores_previous_samples_that_a_later_classification_excluded():
    assert select_refinement_timestamp(5.0, 7.0, [4.0, 6.0]) == 5.5


def test_start_boundary_requires_stable_likely_run_and_negative_neighbor():
    samples = [
        ReplayGameplayBoundarySample(4.0, "ok", "not_gameplay_hud", None),
        ReplayGameplayBoundarySample(6.0, "ok", "likely_gameplay_hud", None),
        ReplayGameplayBoundarySample(7.0, "ok", "likely_gameplay_hud", None),
    ]

    refined, conclusive = derive_refined_boundary(boundary(), "start", samples, 2)

    assert refined == ReplayGameplayBoundary(4.0, 6.0, "between_samples")
    assert conclusive is True


def test_end_boundary_uses_last_stable_likely_sample_before_negative_neighbor():
    samples = [
        ReplayGameplayBoundarySample(4.0, "ok", "likely_gameplay_hud", None),
        ReplayGameplayBoundarySample(5.0, "ok", "likely_gameplay_hud", None),
        ReplayGameplayBoundarySample(6.0, "ok", "not_gameplay_hud", None),
    ]

    refined, conclusive = derive_refined_boundary(boundary(), "end", samples, 2)

    assert refined == ReplayGameplayBoundary(5.0, 6.0, "between_samples")
    assert conclusive is True


def test_unknown_neighbor_preserves_unknown_status_while_bounding_stable_start():
    samples = [
        ReplayGameplayBoundarySample(4.0, "ok", "unknown", None),
        ReplayGameplayBoundarySample(6.0, "ok", "likely_gameplay_hud", None),
        ReplayGameplayBoundarySample(7.0, "ok", "likely_gameplay_hud", None),
    ]

    refined, conclusive = derive_refined_boundary(boundary(), "start", samples, 2)

    assert refined == ReplayGameplayBoundary(4.0, 6.0, "between_samples")
    assert conclusive is False


def test_refines_start_boundary_deterministically_to_configured_tolerance(tmp_path):
    extractor = FakeFrameExtractor()
    detector = SequencedHudDetector([
        "not_gameplay_hud",
        "not_gameplay_hud",
        "likely_gameplay_hud",
        "not_gameplay_hud",
        "not_gameplay_hud",
        "likely_gameplay_hud",
    ])
    config = ReplayGameplayBoundaryRefinementConfig(target_tolerance_seconds=1.0, max_samples=6)

    result = ReplayGameplayBoundaryRefiner(extractor, detector).refine(
        tmp_path / "replay.mp4",
        boundary(),
        "start",
        config,
    )

    assert result.analyzer_version == BOUNDARY_REFINEMENT_ANALYZER_VERSION
    assert result.status == "ok"
    assert result.stop_reason == "tolerance_reached"
    assert result.refined_boundary == ReplayGameplayBoundary(4.0, 5.0, "between_samples")
    assert [sample.timestamp_seconds for sample in result.samples] == [4.0, 2.0, 6.0, 1.0, 3.0, 5.0]
    assert len(extractor.calls) == 6


def test_ambiguous_samples_preserve_range_and_stop_at_sample_limit(tmp_path):
    extractor = FakeFrameExtractor()
    detector = SequencedHudDetector(["unknown", "unknown", "unknown"])
    config = ReplayGameplayBoundaryRefinementConfig(target_tolerance_seconds=0.25, max_samples=3)

    result = ReplayGameplayBoundaryRefiner(extractor, detector).refine(
        tmp_path / "replay.mp4",
        boundary(),
        "start",
        config,
    )

    assert result.status == "unknown"
    assert result.stop_reason == "max_samples_reached"
    assert result.refined_boundary == boundary()
    assert result.unknown_samples == 3
    assert result.failed_samples == 0


def test_all_technical_failures_return_failed_without_becoming_visual_unknown(tmp_path):
    extractor = FakeFrameExtractor({4.0, 2.0})
    detector = SequencedHudDetector([])
    config = ReplayGameplayBoundaryRefinementConfig(target_tolerance_seconds=0.25, max_samples=2)

    result = ReplayGameplayBoundaryRefiner(extractor, detector).refine(
        tmp_path / "replay.mp4",
        boundary(),
        "end",
        config,
    )

    assert result.status == "failed"
    assert result.stop_reason == "max_samples_reached"
    assert result.unknown_samples == 0
    assert result.failed_samples == 2
    assert all(sample.classification is None for sample in result.samples)


def test_mixed_success_and_failure_retains_technical_failure_count(tmp_path):
    extractor = FakeFrameExtractor({1.0})
    detector = SequencedHudDetector([
        "likely_gameplay_hud",
        "likely_gameplay_hud",
        "not_gameplay_hud",
        "likely_gameplay_hud",
    ])
    config = ReplayGameplayBoundaryRefinementConfig(target_tolerance_seconds=1.0, max_samples=5)

    result = ReplayGameplayBoundaryRefiner(extractor, detector).refine(
        tmp_path / "replay.mp4",
        boundary(),
        "end",
        config,
    )

    assert result.status == "unknown"
    assert result.stop_reason == "max_samples_reached"
    assert result.failed_samples == 1
    assert result.refined_boundary == ReplayGameplayBoundary(4.0, 6.0, "between_samples")


def test_refinement_never_samples_outside_original_bracket(tmp_path):
    extractor = FakeFrameExtractor()
    detector = SequencedHudDetector(["unknown"] * 8)

    ReplayGameplayBoundaryRefiner(extractor, detector).refine(
        tmp_path / "replay.mp4",
        boundary(10.0, 12.0),
        "start",
    )

    timestamps = [call["timestamp_seconds"] for call in extractor.calls]
    assert all(10.0 < timestamp < 12.0 for timestamp in timestamps)


def test_temporary_frames_are_removed_after_success_and_failure(tmp_path):
    extractor = FakeFrameExtractor({2.0})
    detector = SequencedHudDetector(["unknown"])
    config = ReplayGameplayBoundaryRefinementConfig(target_tolerance_seconds=0.25, max_samples=2)

    ReplayGameplayBoundaryRefiner(extractor, detector).refine(
        tmp_path / "replay.mp4",
        boundary(),
        "start",
        config,
    )

    assert all(not Path(call["output_path"]).exists() for call in extractor.calls)


@pytest.mark.parametrize(
    ("candidate_boundary", "direction", "config"),
    [
        (boundary(-1.0, 2.0), "start", ReplayGameplayBoundaryRefinementConfig()),
        (boundary(3.0, 2.0), "start", ReplayGameplayBoundaryRefinementConfig()),
        (boundary(), "sideways", ReplayGameplayBoundaryRefinementConfig()),
        (boundary(), "start", ReplayGameplayBoundaryRefinementConfig(target_tolerance_seconds=0.0001)),
        (boundary(), "start", ReplayGameplayBoundaryRefinementConfig(max_samples=0)),
        (boundary(), "start", ReplayGameplayBoundaryRefinementConfig(min_consecutive_likely_samples=1)),
    ],
)
def test_rejects_invalid_requests_before_extraction(candidate_boundary, direction, config, tmp_path):
    extractor = FakeFrameExtractor()

    with pytest.raises(ReplayGameplayBoundaryRefinementError):
        ReplayGameplayBoundaryRefiner(extractor, SequencedHudDetector([])).refine(
            tmp_path / "replay.mp4",
            candidate_boundary,
            direction,
            config,
        )

    assert extractor.calls == []
