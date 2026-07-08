from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class MatchBase(BaseModel):
    player_character: str = Field(min_length=1, max_length=80)
    opponent_character: str = Field(min_length=1, max_length=80)
    result: Literal["win", "loss"]
    played_on: date
    rank_floor: str | None = Field(default=None, max_length=80)
    duration_seconds: int | None = Field(default=None, ge=1)
    notes: str | None = None
    mistake_tags: list[str] = Field(default_factory=list)
    strength_tags: list[str] = Field(default_factory=list)
    reason_for_loss: str | None = Field(default=None, max_length=160)
    practice_next: str | None = None
    replay_filename: str | None = Field(default=None, max_length=255)


class MatchCreate(MatchBase):
    pass


class MatchUpdate(BaseModel):
    player_character: str | None = Field(default=None, min_length=1, max_length=80)
    opponent_character: str | None = Field(default=None, min_length=1, max_length=80)
    result: Literal["win", "loss"] | None = None
    played_on: date | None = None
    rank_floor: str | None = Field(default=None, max_length=80)
    duration_seconds: int | None = Field(default=None, ge=1)
    notes: str | None = None
    mistake_tags: list[str] | None = None
    strength_tags: list[str] | None = None
    reason_for_loss: str | None = Field(default=None, max_length=160)
    practice_next: str | None = None
    replay_filename: str | None = Field(default=None, max_length=255)


class MatchRead(MatchBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
