from typing import Any, Literal

from pydantic import BaseModel, Field


Trend = Literal["improving", "declining", "stable"]
Priority = Literal["high", "medium", "low"]


class PerformanceInsight(BaseModel):
    overall_win_rate: float | None
    recent_5_win_rate: float | None
    recent_10_win_rate: float | None
    previous_10_win_rate: float | None
    performance_trend: Trend | None
    matches_analyzed: int
    trend_sample_size: int
    trend_threshold: float


class StreakInsight(BaseModel):
    longest_win_streak: int
    longest_losing_streak: int
    current_streak_type: Literal["win", "loss"] | None
    current_streak_count: int


class CharacterInsight(BaseModel):
    most_played_character: str | None
    matches: int


class MatchupRecord(BaseModel):
    opponent_character: str
    matches: int
    wins: int
    losses: int
    win_rate: float
    qualified: bool


class MatchupTrend(BaseModel):
    opponent_character: str
    overall_win_rate: float
    recent_win_rate: float
    previous_win_rate: float
    recent_matches: int
    previous_matches: int
    trend: Trend


class MatchupInsights(BaseModel):
    minimum_sample_size: int
    strongest_qualified_matchup: MatchupRecord | None
    weakest_qualified_matchup: MatchupRecord | None
    most_played_matchup: MatchupRecord | None
    matchup_with_most_losses: MatchupRecord | None
    matchups_needing_more_data: list[MatchupRecord]
    matchup_records: list[MatchupRecord]
    recent_matchup_trends: list[MatchupTrend]
    best_matchup: str | None
    worst_matchup: str | None


class MistakePattern(BaseModel):
    tag: str
    count: int
    losses_analyzed: int
    percentage_of_recent_losses: float | None


class PracticePriority(BaseModel):
    practice_next: str
    count: int
    losses_analyzed: int


class Recommendation(BaseModel):
    type: str
    priority: Priority
    title: str
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    sample_size: int


class PatternInsights(BaseModel):
    top_mistake: MistakePattern | None
    overall_mistakes: list[MistakePattern]
    recent_loss_mistakes: list[MistakePattern]
    recent_loss_count: int
    practice_priorities: list[PracticePriority]


class CoachingInsights(BaseModel):
    total_matches: int
    performance: PerformanceInsight
    streaks: StreakInsight
    character: CharacterInsight
    matchups: MatchupInsights
    patterns: PatternInsights
    recommendations: list[Recommendation]
