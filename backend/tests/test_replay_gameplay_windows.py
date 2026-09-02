import pytest

from app.services.replay_gameplay_windows import (
    ReplayGameplayBoundary,
    ReplayGameplayWindowConfig,
    ReplayGameplayWindowError,
    infer_gameplay_windows,
)
from app.services.replay_hud_timeline import ReplayHudTimeline, ReplayHudTimelineSample


def sample(timestamp_seconds: float, code: str) -> ReplayHudTimelineSample:
    if code == "L":
        return ReplayHudTimelineSample(timestamp_seconds, "ok", "likely_gameplay_hud", {"top_left_hud": True}, {"edge": 18.0}, None)
    if code == "N":
        return ReplayHudTimelineSample(timestamp_seconds, "ok", "not_gameplay_hud", {"top_left_hud": False}, {"edge": 2.0}, None)
    if code == "U":
        return ReplayHudTimelineSample(timestamp_seconds, "ok", "unknown", {"transition_hint": True}, {"edge": 8.0}, None)
    if code == "F":
        return ReplayHudTimelineSample(timestamp_seconds, "failed", None, None, None, "Frame extraction failed.")
    raise AssertionError(f"Unknown sample code: {code}")


def timeline(codes: list[str], timestamps: list[float] | None = None, duration_seconds: float | None = None) -> ReplayHudTimeline:
    sample_timestamps = timestamps or [float(index * 2) for index in range(len(codes))]
    duration = duration_seconds if duration_seconds is not None else (sample_timestamps[-1] + 2.0 if sample_timestamps else 10.0)
    return ReplayHudTimeline(
        duration_seconds=duration,
        interval_seconds=2.0,
        start_offset_seconds=0.0,
        samples=[sample(timestamp_seconds, code) for timestamp_seconds, code in zip(sample_timestamps, codes)],
    )


def infer(codes: list[str], timestamps: list[float] | None = None, duration_seconds: float | None = None):
    return infer_gameplay_windows(timeline(codes, timestamps, duration_seconds))


def assert_boundary(boundary: ReplayGameplayBoundary, earliest: float, latest: float, kind: str) -> None:
    assert boundary.earliest_seconds == earliest
    assert boundary.latest_seconds == latest
    assert boundary.kind == kind


def test_no_gameplay_produces_zero_windows():
    result = infer(["N", "N", "U", "F", "N"])

    assert result.samples_analyzed == 5
    assert result.windows == ()


def test_all_likely_gameplay_produces_one_window():
    result = infer(["L", "L", "L"], duration_seconds=8.0)

    assert len(result.windows) == 1
    window = result.windows[0]
    assert_boundary(window.start_boundary, 0.0, 0.0, "starts_at_first_sample")
    assert_boundary(window.end_boundary, 4.0, 8.0, "continues_to_end")
    assert window.supporting_likely_timestamps == (0.0, 2.0, 4.0)


def test_isolated_likely_sample_does_not_create_window():
    result = infer(["N", "N", "L", "N", "N"])

    assert result.windows == ()


def test_exactly_two_consecutive_likely_samples_confirm_window():
    result = infer(["N", "L", "L", "N"])

    assert len(result.windows) == 1
    window = result.windows[0]
    assert_boundary(window.start_boundary, 0.0, 2.0, "between_samples")
    assert_boundary(window.end_boundary, 4.0, 6.0, "between_samples")
    assert window.supporting_likely_timestamps == (2.0, 4.0)


def test_normal_negative_to_likely_to_negative_window():
    result = infer(["N", "N", "L", "L", "L", "N"])

    assert len(result.windows) == 1
    window = result.windows[0]
    assert_boundary(window.start_boundary, 2.0, 4.0, "between_samples")
    assert_boundary(window.end_boundary, 8.0, 10.0, "between_samples")


def test_unknown_before_confirmed_gameplay_sets_start_boundary_from_unknown():
    result = infer(["N", "U", "L", "L", "N"])

    assert len(result.windows) == 1
    assert_boundary(result.windows[0].start_boundary, 2.0, 4.0, "between_samples")


def test_one_unknown_successfully_bridges_likely_regions():
    result = infer(["L", "L", "U", "L", "L"])

    assert len(result.windows) == 1
    window = result.windows[0]
    assert window.supporting_likely_timestamps == (0.0, 2.0, 6.0, 8.0)
    assert window.bridged_unknown_timestamps == (4.0,)
    assert window.bridged_failed_timestamps == ()


def test_two_unknowns_successfully_bridge_likely_regions():
    result = infer(["L", "L", "U", "U", "L", "L"])

    assert len(result.windows) == 1
    assert result.windows[0].bridged_unknown_timestamps == (4.0, 6.0)


def test_three_unknowns_exceed_bridge_and_close_before_unknown_gap():
    result = infer(["L", "L", "U", "U", "U"])

    assert len(result.windows) == 1
    window = result.windows[0]
    assert_boundary(window.end_boundary, 2.0, 4.0, "between_samples")
    assert window.bridged_unknown_timestamps == ()


def test_single_negative_immediately_terminates_window():
    result = infer(["L", "L", "N"])

    assert len(result.windows) == 1
    assert_boundary(result.windows[0].end_boundary, 2.0, 4.0, "between_samples")


def test_negative_allows_later_likely_run_to_become_separate_window():
    result = infer(["L", "L", "N", "L", "L", "N"])

    assert len(result.windows) == 2
    assert result.windows[0].supporting_likely_timestamps == (0.0, 2.0)
    assert result.windows[1].supporting_likely_timestamps == (6.0, 8.0)
    assert_boundary(result.windows[1].start_boundary, 4.0, 6.0, "between_samples")


def test_one_failed_sample_successfully_bridges_likely_regions():
    result = infer(["L", "L", "F", "L", "L"])

    assert len(result.windows) == 1
    assert result.windows[0].bridged_unknown_timestamps == ()
    assert result.windows[0].bridged_failed_timestamps == (4.0,)


def test_two_failed_samples_exceed_bridge_and_close_before_failed_gap():
    result = infer(["L", "L", "F", "F"])

    assert len(result.windows) == 1
    window = result.windows[0]
    assert_boundary(window.end_boundary, 2.0, 4.0, "between_samples")
    assert window.bridged_failed_timestamps == ()


def test_visual_unknown_remains_distinct_from_technical_failed():
    result = infer(["L", "L", "U", "F", "L", "L"])

    assert len(result.windows) == 1
    window = result.windows[0]
    assert window.bridged_unknown_timestamps == (4.0,)
    assert window.bridged_failed_timestamps == (6.0,)


def test_mixed_gap_cannot_bypass_distinct_bridge_limits():
    result = infer(["L", "L", "U", "F", "F", "L", "L"])

    assert len(result.windows) == 2
    assert_boundary(result.windows[0].end_boundary, 2.0, 4.0, "between_samples")
    assert result.windows[0].bridged_unknown_timestamps == ()
    assert result.windows[0].bridged_failed_timestamps == ()
    assert result.windows[1].supporting_likely_timestamps == (10.0, 12.0)


def test_multiple_windows_are_supported():
    result = infer(["N", "N", "L", "L", "L", "N", "N", "L", "L", "L", "N"])

    assert len(result.windows) == 2
    assert result.windows[0].supporting_likely_timestamps == (4.0, 6.0, 8.0)
    assert result.windows[1].supporting_likely_timestamps == (14.0, 16.0, 18.0)


def test_confirmed_gameplay_beginning_with_first_sample_uses_first_sample_boundary():
    result = infer(["L", "L", "N"])

    assert_boundary(result.windows[0].start_boundary, 0.0, 0.0, "starts_at_first_sample")


def test_confirmed_gameplay_continuing_through_final_sample_uses_duration_boundary():
    result = infer(["N", "L", "L"], duration_seconds=7.5)

    assert_boundary(result.windows[0].end_boundary, 4.0, 7.5, "continues_to_end")


def test_unresolved_unknown_gap_at_end_closes_before_gap():
    result = infer(["L", "L", "U", "U"], duration_seconds=10.0)

    assert len(result.windows) == 1
    window = result.windows[0]
    assert_boundary(window.end_boundary, 2.0, 4.0, "between_samples")
    assert window.bridged_unknown_timestamps == ()


def test_unresolved_failed_gap_at_end_closes_before_gap():
    result = infer(["L", "L", "F"], duration_seconds=8.0)

    assert len(result.windows) == 1
    window = result.windows[0]
    assert_boundary(window.end_boundary, 2.0, 4.0, "between_samples")
    assert window.bridged_failed_timestamps == ()


def test_irregular_timestamps_are_used_in_boundaries():
    result = infer(["N", "U", "L", "L", "N"], timestamps=[0.0, 1.5, 4.25, 7.75, 9.0], duration_seconds=12.0)

    assert len(result.windows) == 1
    assert_boundary(result.windows[0].start_boundary, 1.5, 4.25, "between_samples")
    assert_boundary(result.windows[0].end_boundary, 7.75, 9.0, "between_samples")


def test_empty_timeline_is_valid_and_produces_zero_windows():
    result = infer_gameplay_windows(timeline([], duration_seconds=12.0))

    assert result.duration_seconds == 12.0
    assert result.samples_analyzed == 0
    assert result.windows == ()


def test_invalid_duration_is_rejected():
    with pytest.raises(ReplayGameplayWindowError, match="duration"):
        infer_gameplay_windows(timeline(["L", "L"], duration_seconds=0))


def test_unsorted_timestamps_are_rejected():
    with pytest.raises(ReplayGameplayWindowError, match="strictly ascending"):
        infer(["L", "L"], timestamps=[2.0, 1.0], duration_seconds=10.0)


def test_duplicate_timestamps_are_rejected():
    with pytest.raises(ReplayGameplayWindowError, match="strictly ascending"):
        infer(["L", "L"], timestamps=[2.0, 2.0], duration_seconds=10.0)


def test_timestamp_at_or_after_duration_is_rejected():
    with pytest.raises(ReplayGameplayWindowError, match="before the end"):
        infer(["L"], timestamps=[10.0], duration_seconds=10.0)


@pytest.mark.parametrize(
    "config",
    [
        ReplayGameplayWindowConfig(min_consecutive_likely_samples=1),
        ReplayGameplayWindowConfig(max_unknown_bridge_samples=-1),
        ReplayGameplayWindowConfig(max_failed_bridge_samples=-1),
        ReplayGameplayWindowConfig(negative_samples_to_terminate=2),
    ],
)
def test_invalid_config_is_rejected(config: ReplayGameplayWindowConfig):
    with pytest.raises(ReplayGameplayWindowError):
        infer_gameplay_windows(timeline(["L", "L"]), config)


def test_invalid_status_classification_combinations_are_rejected():
    invalid = ReplayHudTimeline(
        duration_seconds=10.0,
        interval_seconds=2.0,
        start_offset_seconds=0.0,
        samples=[ReplayHudTimelineSample(0.0, "failed", "likely_gameplay_hud", None, None, "bad")],
    )

    with pytest.raises(ReplayGameplayWindowError, match="Failed"):
        infer_gameplay_windows(invalid)


def test_supporting_and_bridged_timestamps_are_separated():
    result = infer(["L", "L", "U", "F", "L", "L", "N"])

    window = result.windows[0]
    assert window.supporting_likely_timestamps == (0.0, 2.0, 8.0, 10.0)
    assert window.bridged_unknown_timestamps == (4.0,)
    assert window.bridged_failed_timestamps == (6.0,)


def test_inference_does_not_mutate_input_timeline():
    input_timeline = timeline(["L", "L", "U", "L"])
    original_samples = tuple(input_timeline.samples)

    infer_gameplay_windows(input_timeline)

    assert tuple(input_timeline.samples) == original_samples
