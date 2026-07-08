from app.schemas.match import MatchRead
from pydantic import BaseModel


class CharacterWinRate(BaseModel):
    opponent_character: str
    matches: int
    wins: int
    win_rate: float


class TagCount(BaseModel):
    label: str
    count: int


class DashboardStats(BaseModel):
    total_matches: int
    wins: int
    losses: int
    win_rate: float
    win_rate_by_opponent: list[CharacterWinRate]
    most_common_mistake_tags: list[TagCount]
    most_common_reason_for_loss: TagCount | None
    recent_matches: list[MatchRead]
