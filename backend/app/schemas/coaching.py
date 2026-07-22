from pydantic import BaseModel


class CoachingInsights(BaseModel):
    overallWinRate: float
    longest_win_streak: int
    longest_losing_streak: int
    current_streak_type: str | None
    current_streak_count: int
    mostPlayedCharacter: str | None
    bestMatchup: str | None
    worstMatchup: str | None
    totalMatches: int
