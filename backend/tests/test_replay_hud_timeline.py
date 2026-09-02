from pathlib import Path

import pytest

from app.services.frame_extraction import FrameExtractionError
from app.services.ggst_hud_detection import GGSTHudDetectionError, GGSTHudDetectionResult
from app.services.replay_hud_timeline import (
    ReplayHudTimelineError,
    ReplayHudTimelineScanner,
    generate_replay_sample_timestamps,
)


class FakeFrameExtractor:
    def __init__(self, error_on_calls: set[int] | None = None) -> None:
        self.error_on_calls = error_on_calls or set()
        self.calls: list[dict] = []

    def extract_jpeg_frame(self, video_path: str | Path, timestamp_seconds: float, output_path: str | Path) -> None:
        self.calls.append({"video_path": str(video_path), "timestamp_seconds": timestamp_seconds, "output_path": str(output_path)})
        if len(self.calls) in self.error_on_calls:
            raise FrameExtractionError("Frame extraction failed.")
        Path(output_path).write_bytes(b"\xff\xd8fake frame\xff\xd9")


class FakeHudDetector:
    def __init__(self, results: list[GGSTHudDetectionResult] | None = None, error_on_calls: set[int] | None = None) -> None:
        self.results = results or [hud_result("likely_gameplay_hud")]
        self.error_on_calls = error_on_calls or set()
        self.calls: list[dict] = []

    def detect(self, image_path: str | Path) -> GGSTHudDetectionResult:
        path = Path(image_path)
        self.calls.append({"image_path": str(path), "exists_during_detection": path.exists()})
        if len(self.calls) in self.error_on_calls:
            raise GGSTHudDetectionError("HUD detection image could not be read.")
        return self.results[min(len(self.calls) - 1, len(self.results) - 1)]


def hud_result(classification: str) -> GGSTHudDetectionResult:
    return GGSTHudDetectionResult(
        classification=classification,
        evidence={
            "top_left_hud": classification == "likely_gameplay_hud",
            "top_right_hud": classification == "likely_gameplay_hud",
            "top_center_support": classification == "likely_gameplay_hud",
            "bottom_support": classification != "not_gameplay_hud",
            "transition_hint": classification == "unknown",
            "bilateral_top_hud": classification == "likely_gameplay_hud",
            "blank_frame": False,
        },
        measurements={
            "top_left_horizontal_edge_score": 18.0 if classification == "likely_gameplay_hud" else 4.0,
            "top_center_horizontal_edge_score": 14.0 if classification == "likely_gameplay_hud" else 6.0,
        },
    )


def test_generates_deterministic_timestamps_for_normal_duration():
    assert generate_replay_sample_timestamps(10.0, 2.0) == [0.0, 2.0, 4.0, 6.0, 8.0]


def test_excludes_exact_end_timestamp():
    assert generate_replay_sample_timestamps(10.0, 5.0) == [0.0, 5.0]


def test_final_partial_interval_is_included_before_duration():
    assert generate_replay_sample_timestamps(10.5, 5.0) == [0.0, 5.0, 10.0]


def test_supports_zero_and_explicit_nonzero_start_offsets():
    assert generate_replay_sample_timestamps(6.0, 2.0, start_offset_seconds=0.0) == [0.0, 2.0, 4.0]
    assert generate_replay_sample_timestamps(6.0, 2.0, start_offset_seconds=1.0) == [1.0, 3.0, 5.0]


def test_generates_one_sample_for_very_short_valid_video():
    assert generate_replay_sample_timestamps(0.5, 2.0) == [0.0]


@pytest.mark.parametrize("duration_seconds", [0, -1, float("inf"), float("nan"), "nope"])
def test_rejects_invalid_duration(duration_seconds):
    with pytest.raises(ReplayHudTimelineError, match="Duration"):
        generate_replay_sample_timestamps(duration_seconds, 1.0)


@pytest.mark.parametrize("interval_seconds", [0, -1, float("inf"), float("nan"), "nope"])
def test_rejects_invalid_interval(interval_seconds):
    with pytest.raises(ReplayHudTimelineError, match="Interval"):
        generate_replay_sample_timestamps(10.0, interval_seconds)


@pytest.mark.parametrize("start_offset_seconds", [-1, float("inf"), float("nan"), "nope"])
def test_rejects_invalid_start_offset(start_offset_seconds):
    with pytest.raises(ReplayHudTimelineError, match="Start offset"):
        generate_replay_sample_timestamps(10.0, 1.0, start_offset_seconds=start_offset_seconds)


def test_rejects_start_offset_at_or_after_duration():
    with pytest.raises(ReplayHudTimelineError, match="Start offset must be before"):
        generate_replay_sample_timestamps(10.0, 1.0, start_offset_seconds=10.0)
    with pytest.raises(ReplayHudTimelineError, match="Start offset must be before"):
        generate_replay_sample_timestamps(10.0, 1.0, start_offset_seconds=11.0)


@pytest.mark.parametrize("max_samples", [0, -1])
def test_rejects_invalid_max_samples(max_samples: int):
    with pytest.raises(ReplayHudTimelineError, match="Maximum samples"):
        generate_replay_sample_timestamps(10.0, 1.0, max_samples=max_samples)


def test_rejects_timeline_that_exceeds_max_samples_without_truncating():
    with pytest.raises(ReplayHudTimelineError, match="maximum sample count"):
        generate_replay_sample_timestamps(10.0, 2.0, max_samples=4)


def test_rounds_timestamps_to_milliseconds_for_floating_point_stability():
    assert generate_replay_sample_timestamps(1.0, 0.333333) == [0.0, 0.333, 0.667]


def test_rejects_intervals_too_small_for_millisecond_precision():
    with pytest.raises(ReplayHudTimelineError, match="too small"):
        generate_replay_sample_timestamps(0.002, 0.0004)


def test_scanner_returns_successful_multi_sample_timeline_in_order(tmp_path):
    video_path = tmp_path / "replay.mp4"
    video_path.write_bytes(b"fake video")
    extractor = FakeFrameExtractor()
    detector = FakeHudDetector([
        hud_result("likely_gameplay_hud"),
        hud_result("not_gameplay_hud"),
        hud_result("unknown"),
    ])

    timeline = ReplayHudTimelineScanner(extractor, detector).scan(video_path, duration_seconds=6.0, interval_seconds=2.0)

    assert timeline.duration_seconds == 6.0
    assert timeline.interval_seconds == 2.0
    assert timeline.start_offset_seconds == 0.0
    assert [sample.timestamp_seconds for sample in timeline.samples] == [0.0, 2.0, 4.0]
    assert [sample.status for sample in timeline.samples] == ["ok", "ok", "ok"]
    assert [sample.classification for sample in timeline.samples] == ["likely_gameplay_hud", "not_gameplay_hud", "unknown"]
    assert timeline.samples[0].evidence is not None
    assert timeline.samples[0].measurements is not None
    assert timeline.samples[0].error is None
    assert [call["timestamp_seconds"] for call in extractor.calls] == [0.0, 2.0, 4.0]
    assert len(detector.calls) == 3
    assert all(call["exists_during_detection"] for call in detector.calls)


def test_scanner_uses_explicit_start_offset(tmp_path):
    video_path = tmp_path / "replay.mp4"
    video_path.write_bytes(b"fake video")
    extractor = FakeFrameExtractor()
    detector = FakeHudDetector()

    timeline = ReplayHudTimelineScanner(extractor, detector).scan(
        video_path,
        duration_seconds=7.0,
        interval_seconds=2.0,
        start_offset_seconds=1.0,
    )

    assert [sample.timestamp_seconds for sample in timeline.samples] == [1.0, 3.0, 5.0]
    assert [call["timestamp_seconds"] for call in extractor.calls] == [1.0, 3.0, 5.0]


def test_extraction_failure_becomes_failed_sample_and_later_timestamps_continue(tmp_path):
    video_path = tmp_path / "replay.mp4"
    video_path.write_bytes(b"fake video")
    extractor = FakeFrameExtractor(error_on_calls={2})
    detector = FakeHudDetector([hud_result("likely_gameplay_hud"), hud_result("unknown")])

    timeline = ReplayHudTimelineScanner(extractor, detector).scan(video_path, duration_seconds=6.0, interval_seconds=2.0)

    assert [sample.timestamp_seconds for sample in timeline.samples] == [0.0, 2.0, 4.0]
    assert [sample.status for sample in timeline.samples] == ["ok", "failed", "ok"]
    failed = timeline.samples[1]
    assert failed.classification is None
    assert failed.evidence is None
    assert failed.measurements is None
    assert failed.error == "Frame extraction failed."
    assert [call["timestamp_seconds"] for call in extractor.calls] == [0.0, 2.0, 4.0]
    assert len(detector.calls) == 2


def test_detector_failure_becomes_failed_sample_and_later_timestamps_continue(tmp_path):
    video_path = tmp_path / "replay.mp4"
    video_path.write_bytes(b"fake video")
    extractor = FakeFrameExtractor()
    detector = FakeHudDetector([hud_result("likely_gameplay_hud"), hud_result("not_gameplay_hud")], error_on_calls={2})

    timeline = ReplayHudTimelineScanner(extractor, detector).scan(video_path, duration_seconds=6.0, interval_seconds=2.0)

    assert [sample.status for sample in timeline.samples] == ["ok", "failed", "ok"]
    failed = timeline.samples[1]
    assert failed.classification is None
    assert failed.evidence is None
    assert failed.measurements is None
    assert failed.error == "HUD detection image could not be read."
    assert len(extractor.calls) == 3
    assert len(detector.calls) == 3


def test_temp_frames_are_cleaned_on_success_and_failure(tmp_path):
    video_path = tmp_path / "replay.mp4"
    video_path.write_bytes(b"fake video")
    extractor = FakeFrameExtractor()
    detector = FakeHudDetector(error_on_calls={2})

    ReplayHudTimelineScanner(extractor, detector).scan(video_path, duration_seconds=6.0, interval_seconds=2.0)

    assert all(Path(call["output_path"]).exists() is False for call in extractor.calls)
    assert all(Path(call["image_path"]).exists() is False for call in detector.calls)


def test_scanner_does_not_mutate_or_delete_input_replay_file(tmp_path):
    video_path = tmp_path / "replay.mp4"
    video_path.write_bytes(b"original video")

    ReplayHudTimelineScanner(FakeFrameExtractor(), FakeHudDetector()).scan(video_path, duration_seconds=2.0, interval_seconds=1.0)

    assert video_path.read_bytes() == b"original video"


def test_invalid_scan_configuration_fails_before_extracting(tmp_path):
    video_path = tmp_path / "replay.mp4"
    video_path.write_bytes(b"fake video")
    extractor = FakeFrameExtractor()
    detector = FakeHudDetector()

    with pytest.raises(ReplayHudTimelineError):
        ReplayHudTimelineScanner(extractor, detector).scan(video_path, duration_seconds=10.0, interval_seconds=1.0, max_samples=2)

    assert extractor.calls == []
    assert detector.calls == []


def test_module_has_no_r2_storage_or_api_dependency():
    import app.services.replay_hud_timeline as timeline_module

    module_source = Path(timeline_module.__file__).read_text()

    assert "app.api" not in module_source
    assert "storage" not in module_source.lower()
    assert "boto" not in module_source.lower()
