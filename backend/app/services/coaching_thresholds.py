"""Deterministic coaching thresholds.

These constants intentionally keep weak evidence from being presented as strong
coaching. They are centralized so future replay-derived analysis can reuse the
same confidence rules instead of scattering magic numbers through the service.
"""

# Recent windows mirror common review habits: last few sets, last session-sized
# sample, and the preceding baseline window.
RECENT_5_MATCHES = 5
RECENT_10_MATCHES = 10
PREVIOUS_10_MATCHES = 10

# A 15 percentage-point swing is large enough to be actionable while avoiding
# overreacting to normal variance.
PERFORMANCE_TREND_THRESHOLD = 15.0

# Three sets is the first point where matchup labels are more useful than noise.
MIN_MATCHUP_SAMPLE = 3

# Recent matchup trends need enough total history and at least two recent sets
# against the same character.
MIN_MATCHUP_TREND_TOTAL = 6
RECENT_MATCHUP_WINDOW = 3
MATCHUP_TREND_THRESHOLD = 20.0

# Two repeated tags/practice notes are worth surfacing as an emerging pattern.
MIN_REPEATED_MISTAKE_COUNT = 2
MIN_REPEATED_PRACTICE_COUNT = 2
RECENT_LOSS_WINDOW = 10

# Keep the Coaching page focused instead of burying the player in every finding.
MAX_RECOMMENDATIONS = 5
MAX_PATTERN_ITEMS = 5
