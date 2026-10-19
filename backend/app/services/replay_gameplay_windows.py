import math
from dataclasses import dataclass
from typing import Literal

from app.services.replay_hud_timeline import ReplayHudTimeline, ReplayHudTimelineSample

GameplayBoundaryKind = Literal["starts_at_first_sample", "between_samples", "continues_to_end"]

DEFAULT_MIN_CONSECUTIVE_LIKELY_SAMPLES = 2
DEFAULT_MAX_UNKNOWN_BRIDGE_SAMPLES = 2
DEFAULT_MAX_FAILED_BRIDGE_SAMPLES = 1
DEFAULT_NEGATIVE_SAMPLES_TO_TERMINATE = 1


class ReplayGameplayWindowError(RuntimeError):
    def __init__(self, public_message: str) -> None:
        super().__init__(public_message)
        self.public_message = public_message


@dataclass(frozen=True)
class ReplayGameplayWindowConfig:
    """Rules for confirming gameplay and bridging inconclusive timeline samples."""

    min_consecutive_likely_samples: int = DEFAULT_MIN_CONSECUTIVE_LIKELY_SAMPLES
    max_unknown_bridge_samples: int = DEFAULT_MAX_UNKNOWN_BRIDGE_SAMPLES
    max_failed_bridge_samples: int = DEFAULT_MAX_FAILED_BRIDGE_SAMPLES
    negative_samples_to_terminate: int = DEFAULT_NEGATIVE_SAMPLES_TO_TERMINATE


@dataclass(frozen=True)
class ReplayGameplayBoundary:
    """An uncertainty range containing a sampled gameplay transition.

    For example, ``earliest_seconds=10`` and ``latest_seconds=12`` means the
    transition occurred somewhere in ``[10s, 12s]``. It is not an estimate that
    the transition happened at the midpoint.
    """

    earliest_seconds: float
    latest_seconds: float
    kind: GameplayBoundaryKind


@dataclass(frozen=True)
class ReplayGameplayWindow:
    """A coarse gameplay interval and the timeline evidence supporting it."""

    start_boundary: ReplayGameplayBoundary
    end_boundary: ReplayGameplayBoundary
    supporting_likely_timestamps: tuple[float, ...]
    bridged_unknown_timestamps: tuple[float, ...]
    bridged_failed_timestamps: tuple[float, ...]


@dataclass(frozen=True)
class ReplayGameplayWindowResult:
    """All coarse gameplay windows inferred from one validated timeline."""

    duration_seconds: float
    samples_analyzed: int
    windows: tuple[ReplayGameplayWindow, ...]


@dataclass
class WindowDraft:
    """Mutable internal state used only while one gameplay window is being built."""

    start_boundary: ReplayGameplayBoundary
    supporting_likely_timestamps: list[float]
    bridged_unknown_timestamps: list[float]
    bridged_failed_timestamps: list[float]
    last_confirmed_gameplay_timestamp: float


def infer_gameplay_windows(
    timeline: ReplayHudTimeline,
    config: ReplayGameplayWindowConfig | None = None,
) -> ReplayGameplayWindowResult:
    """Infer coarse gameplay ranges without claiming unsampled precision.

    The loop acts as a small state machine:

    * ``pending_likely_run`` waits for enough consecutive likely samples to
      confirm that gameplay has begun.
    * ``active_window`` accumulates evidence for confirmed gameplay.
    * ``pending_gap`` temporarily holds unknown or failed samples. The gap is
      included only if later likely evidence confirms gameplay resumed.

    Negative evidence closes an active window. Unknown visual evidence and
    technical failures follow similar control flow but remain separately recorded.
    """

    rules = config or ReplayGameplayWindowConfig()
    validate_timeline(timeline)
    validate_config(rules)

    windows: list[ReplayGameplayWindow] = []
    active_window: WindowDraft | None = None
    pending_likely_run: list[ReplayHudTimelineSample] = []
    pending_gap: list[ReplayHudTimelineSample] = []
    previous_sample: ReplayHudTimelineSample | None = None

    for sample in timeline.samples:
        if is_likely_sample(sample):
            if active_window is None:
                pending_likely_run.append(sample)
                if len(pending_likely_run) >= rules.min_consecutive_likely_samples:
                    first_likely = pending_likely_run[0]
                    # The boundary starts before the first sample in the confirmed
                    # run, not before the sample that happened to meet the threshold.
                    active_window = WindowDraft(
                        start_boundary=start_boundary_for(first_likely, previous_sample_before_run(timeline.samples, first_likely)),
                        supporting_likely_timestamps=[likely.timestamp_seconds for likely in pending_likely_run],
                        bridged_unknown_timestamps=[],
                        bridged_failed_timestamps=[],
                        last_confirmed_gameplay_timestamp=sample.timestamp_seconds,
                    )
                    pending_likely_run = []
            else:
                if pending_gap:
                    # Later likely evidence proves the bounded gap was surrounded
                    # by gameplay, so it can now be retained inside this window.
                    commit_pending_gap(active_window, pending_gap)
                    pending_gap = []
                active_window.supporting_likely_timestamps.append(sample.timestamp_seconds)
                active_window.last_confirmed_gameplay_timestamp = sample.timestamp_seconds
        elif is_unknown_sample(sample):
            pending_likely_run = []
            if active_window is not None:
                pending_gap.append(sample)
                if not can_bridge_gap(pending_gap, rules):
                    # Once ambiguity exceeds the configured allowance, stop at the
                    # first gap sample rather than inventing evidence inside it.
                    windows.append(finalize_window(active_window, unbridgeable_gap_boundary(active_window, pending_gap[0])))
                    active_window = None
                    pending_gap = []
        elif is_failed_sample(sample):
            pending_likely_run = []
            if active_window is not None:
                pending_gap.append(sample)
                if not can_bridge_gap(pending_gap, rules):
                    # Failed extraction is not negative visual evidence. It still
                    # limits how far the current window can be supported.
                    windows.append(finalize_window(active_window, unbridgeable_gap_boundary(active_window, pending_gap[0])))
                    active_window = None
                    pending_gap = []
        elif is_negative_sample(sample):
            pending_likely_run = []
            if active_window is not None:
                if pending_gap:
                    # A negative after an unresolved gap cannot locate the end more
                    # precisely than the start of that gap.
                    windows.append(finalize_window(active_window, unresolved_gap_boundary(active_window, pending_gap[0])))
                    pending_gap = []
                else:
                    windows.append(finalize_window(active_window, terminating_negative_boundary(active_window, sample)))
                active_window = None
        else:
            raise ReplayGameplayWindowError("Timeline sample has an invalid status or classification.")

        previous_sample = sample

    if active_window is not None:
        if pending_gap:
            # With no later sample to resolve the gap, preserve the last supported
            # range instead of assuming gameplay continued through it.
            windows.append(finalize_window(active_window, unresolved_gap_boundary(active_window, pending_gap[0])))
        else:
            windows.append(finalize_window(active_window, continues_to_end_boundary(active_window, timeline.duration_seconds)))

    return ReplayGameplayWindowResult(
        duration_seconds=timeline.duration_seconds,
        samples_analyzed=len(timeline.samples),
        windows=tuple(windows),
    )


def is_likely_sample(sample: ReplayHudTimelineSample) -> bool:
    return sample.status == "ok" and sample.classification == "likely_gameplay_hud"


def is_unknown_sample(sample: ReplayHudTimelineSample) -> bool:
    return sample.status == "ok" and sample.classification == "unknown"


def is_negative_sample(sample: ReplayHudTimelineSample) -> bool:
    return sample.status == "ok" and sample.classification == "not_gameplay_hud"


def is_failed_sample(sample: ReplayHudTimelineSample) -> bool:
    return sample.status == "failed"


def previous_sample_before_run(
    samples: list[ReplayHudTimelineSample],
    first_likely: ReplayHudTimelineSample,
) -> ReplayHudTimelineSample | None:
    first_index = samples.index(first_likely)
    if first_index == 0:
        return None
    return samples[first_index - 1]


def start_boundary_for(
    first_likely: ReplayHudTimelineSample,
    previous_sample: ReplayHudTimelineSample | None,
) -> ReplayGameplayBoundary:
    """Bracket gameplay start using the sample before the first likely evidence."""

    if previous_sample is None:
        # Gameplay was visible in the first available sample, so no earlier
        # non-gameplay observation exists to refine the start.
        return ReplayGameplayBoundary(
            earliest_seconds=0.0,
            latest_seconds=first_likely.timestamp_seconds,
            kind="starts_at_first_sample",
        )
    return ReplayGameplayBoundary(
        earliest_seconds=previous_sample.timestamp_seconds,
        latest_seconds=first_likely.timestamp_seconds,
        kind="between_samples",
    )


def can_bridge_gap(
    pending_gap: list[ReplayHudTimelineSample],
    config: ReplayGameplayWindowConfig,
) -> bool:
    """Check unknown and failed allowances independently to preserve provenance."""

    unknown_count = sum(1 for sample in pending_gap if is_unknown_sample(sample))
    failed_count = sum(1 for sample in pending_gap if is_failed_sample(sample))
    return unknown_count <= config.max_unknown_bridge_samples and failed_count <= config.max_failed_bridge_samples


def commit_pending_gap(active_window: WindowDraft, pending_gap: list[ReplayHudTimelineSample]) -> None:
    for sample in pending_gap:
        if is_unknown_sample(sample):
            active_window.bridged_unknown_timestamps.append(sample.timestamp_seconds)
            active_window.last_confirmed_gameplay_timestamp = sample.timestamp_seconds
        elif is_failed_sample(sample):
            active_window.bridged_failed_timestamps.append(sample.timestamp_seconds)
            active_window.last_confirmed_gameplay_timestamp = sample.timestamp_seconds


def unbridgeable_gap_boundary(
    active_window: WindowDraft,
    first_gap_sample: ReplayHudTimelineSample,
) -> ReplayGameplayBoundary:
    return ReplayGameplayBoundary(
        earliest_seconds=active_window.last_confirmed_gameplay_timestamp,
        latest_seconds=first_gap_sample.timestamp_seconds,
        kind="between_samples",
    )


def unresolved_gap_boundary(
    active_window: WindowDraft,
    first_gap_sample: ReplayHudTimelineSample,
) -> ReplayGameplayBoundary:
    return ReplayGameplayBoundary(
        earliest_seconds=active_window.last_confirmed_gameplay_timestamp,
        latest_seconds=first_gap_sample.timestamp_seconds,
        kind="between_samples",
    )


def terminating_negative_boundary(
    active_window: WindowDraft,
    negative_sample: ReplayHudTimelineSample,
) -> ReplayGameplayBoundary:
    return ReplayGameplayBoundary(
        earliest_seconds=active_window.last_confirmed_gameplay_timestamp,
        latest_seconds=negative_sample.timestamp_seconds,
        kind="between_samples",
    )


def continues_to_end_boundary(
    active_window: WindowDraft,
    duration_seconds: float,
) -> ReplayGameplayBoundary:
    return ReplayGameplayBoundary(
        earliest_seconds=active_window.last_confirmed_gameplay_timestamp,
        latest_seconds=duration_seconds,
        kind="continues_to_end",
    )


def finalize_window(
    active_window: WindowDraft,
    end_boundary: ReplayGameplayBoundary,
) -> ReplayGameplayWindow:
    return ReplayGameplayWindow(
        start_boundary=active_window.start_boundary,
        end_boundary=end_boundary,
        supporting_likely_timestamps=tuple(active_window.supporting_likely_timestamps),
        bridged_unknown_timestamps=tuple(active_window.bridged_unknown_timestamps),
        bridged_failed_timestamps=tuple(active_window.bridged_failed_timestamps),
    )


def validate_timeline(timeline: ReplayHudTimeline) -> None:
    """Reject evidence that cannot form a trustworthy chronological timeline."""

    if not math.isfinite(timeline.duration_seconds) or timeline.duration_seconds <= 0:
        raise ReplayGameplayWindowError("Timeline duration must be a finite number greater than 0.")

    previous_timestamp: float | None = None
    for sample in timeline.samples:
        timestamp = sample.timestamp_seconds
        if not math.isfinite(timestamp) or timestamp < 0:
            raise ReplayGameplayWindowError("Timeline sample timestamps must be finite numbers greater than or equal to 0.")
        if timestamp >= timeline.duration_seconds:
            raise ReplayGameplayWindowError("Timeline sample timestamps must be before the end of the video.")
        if previous_timestamp is not None and timestamp <= previous_timestamp:
            raise ReplayGameplayWindowError("Timeline sample timestamps must be strictly ascending.")
        if sample.status == "ok" and sample.classification not in {"likely_gameplay_hud", "not_gameplay_hud", "unknown"}:
            raise ReplayGameplayWindowError("Successful timeline samples must include a valid HUD classification.")
        if sample.status == "failed" and sample.classification is not None:
            raise ReplayGameplayWindowError("Failed timeline samples must not include a HUD classification.")
        if sample.status not in {"ok", "failed"}:
            raise ReplayGameplayWindowError("Timeline sample status is invalid.")
        previous_timestamp = timestamp


def validate_config(config: ReplayGameplayWindowConfig) -> None:
    if type(config.min_consecutive_likely_samples) is not int or config.min_consecutive_likely_samples < 2:
        raise ReplayGameplayWindowError("Minimum consecutive likely samples must be an integer greater than or equal to 2.")
    if type(config.max_unknown_bridge_samples) is not int or config.max_unknown_bridge_samples < 0:
        raise ReplayGameplayWindowError("Maximum unknown bridge samples must be a non-negative integer.")
    if type(config.max_failed_bridge_samples) is not int or config.max_failed_bridge_samples < 0:
        raise ReplayGameplayWindowError("Maximum failed bridge samples must be a non-negative integer.")
    if type(config.negative_samples_to_terminate) is not int or config.negative_samples_to_terminate != 1:
        raise ReplayGameplayWindowError("Negative samples to terminate must be exactly 1 for coarse gameplay-window inference.")



"""Identify where gameplay likely starts and ends in a GGST replay.

This module uses HUD detection results from multiple video timestamps
to find sections where gameplay is likely happening.

It requires multiple consecutive gameplay detections to confirm a
gameplay window. It also allows a limited number of unknown or failed
detections without immediately ending the window.

Returns estimated gameplay start and end times, along with the evidence
used to identify them. These times are approximate and can be made
more accurate in later stages of replay analysis.
"""
