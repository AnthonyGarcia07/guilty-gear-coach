from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

MIN_MATCH_DATE = date(2021, 6, 11)
MAX_DURATION_SECONDS = 60 * 30
MAX_SET_SCORE = 10
MAX_TAGS = 12
MAX_TAG_LENGTH = 40
VALID_RANKS = (
    "Iron",
    "Bronze",
    "Silver",
    "Gold",
    "Platinum",
    "Diamond",
    "Master",
    "Grand Master",
    "Celestial",
    "Vanquisher",
)
VALID_CHARACTERS = {
    "Sol Badguy",
    "Ky Kiske",
    "May",
    "Axl Low",
    "Chipp Zanuff",
    "Potemkin",
    "Faust",
    "Millia Rage",
    "Zato-1",
    "Ramlethal Valentine",
    "Leo Whitefang",
    "Nagoriyuki",
    "Giovanna",
    "Anji Mito",
    "I-No",
    "Goldlewis Dickinson",
    "Jack-O'",
    "Happy Chaos",
    "Baiken",
    "Testament",
    "Bridget",
    "Sin Kiske",
    "Bedman?",
    "Asuka R#",
    "Johnny",
    "Elphelt Valentine",
    "A.B.A",
    "Slayer",
    "Queen Dizzy",
    "Venom",
    "Unika",
    "Lucy",
    "Jam Kuradoberi",
    "Robo-Ky",
    "Dizzy",
    "Jack-O",
}


def clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def validate_character(value: str) -> str:
    cleaned = value.strip()
    if cleaned not in VALID_CHARACTERS:
        raise ValueError("Select a supported Guilty Gear Strive character.")
    return cleaned


def validate_required_rank(value: str | None) -> str:
    cleaned = clean_optional_text(value)
    if cleaned is None:
        raise ValueError("Select a rank.")
    if cleaned not in VALID_RANKS:
        raise ValueError("Select a valid Guilty Gear Strive rank.")
    return cleaned


def validate_played_on(value: date) -> date:
    if value < MIN_MATCH_DATE:
        raise ValueError("Match date cannot be before Guilty Gear Strive's June 11, 2021 release.")
    if value > date.today():
        raise ValueError("Match date cannot be in the future.")
    return value


def validate_tags(value: list[str] | None) -> list[str] | None:
    if value is None:
        return None
    cleaned = []
    for tag in value:
        normalized = tag.strip()
        if normalized and normalized not in cleaned:
            cleaned.append(normalized)
    if len(cleaned) > MAX_TAGS:
        raise ValueError(f"Use no more than {MAX_TAGS} tags.")
    if any(len(tag) > MAX_TAG_LENGTH for tag in cleaned):
        raise ValueError(f"Tags must be {MAX_TAG_LENGTH} characters or fewer.")
    return cleaned


def validate_completed_set_score(result: str | None, rounds_won: int | None, rounds_lost: int | None, first_to: int | None) -> None:
    score_values = (rounds_won, rounds_lost, first_to)
    if all(value is None for value in score_values):
        return
    if any(value is None for value in score_values):
        raise ValueError("Enter rounds won, rounds lost, and first-to together for the completed set score.")
    if rounds_won == rounds_lost:
        raise ValueError("Completed set score cannot be tied.")
    if max(rounds_won, rounds_lost) != first_to:
        raise ValueError("Completed set score must have exactly one side reaching the selected first-to value.")
    if min(rounds_won, rounds_lost) >= first_to:
        raise ValueError("The losing side must finish below the selected first-to value.")
    if result == "win" and rounds_won <= rounds_lost:
        raise ValueError("A win must have your score ahead of the opponent.")
    if result == "loss" and rounds_lost <= rounds_won:
        raise ValueError("A loss must have the opponent score ahead of yours.")


class MatchBase(BaseModel):
    player_character: str = Field(min_length=1, max_length=80)
    opponent_character: str = Field(min_length=1, max_length=80)
    result: Literal["win", "loss"]
    played_on: date
    rank_floor: str = Field(min_length=1, max_length=80)
    duration_seconds: int = Field(ge=1, le=MAX_DURATION_SECONDS)
    rounds_won: int | None = Field(default=None, ge=0, le=MAX_SET_SCORE)
    rounds_lost: int | None = Field(default=None, ge=0, le=MAX_SET_SCORE)
    first_to: int | None = Field(default=None, gt=0, le=MAX_SET_SCORE)
    notes: str | None = Field(default=None, max_length=2000)
    mistake_tags: list[str] = Field(default_factory=list)
    strength_tags: list[str] = Field(default_factory=list)
    reason_for_loss: str | None = Field(default=None, max_length=160)
    practice_next: str | None = Field(default=None, max_length=1000)
    replay_filename: str | None = Field(default=None, max_length=255)

    _validate_player_character = field_validator("player_character")(validate_character)
    _validate_opponent_character = field_validator("opponent_character")(validate_character)
    _validate_rank_floor = field_validator("rank_floor")(validate_required_rank)
    _validate_played_on = field_validator("played_on")(validate_played_on)
    _clean_notes = field_validator("notes")(clean_optional_text)
    _clean_reason_for_loss = field_validator("reason_for_loss")(clean_optional_text)
    _clean_practice_next = field_validator("practice_next")(clean_optional_text)
    _clean_replay_filename = field_validator("replay_filename")(clean_optional_text)
    _validate_mistake_tags = field_validator("mistake_tags")(validate_tags)
    _validate_strength_tags = field_validator("strength_tags")(validate_tags)

    @model_validator(mode="after")
    def validate_score(self) -> "MatchBase":
        validate_completed_set_score(self.result, self.rounds_won, self.rounds_lost, self.first_to)
        return self


class MatchCreate(MatchBase):
    pass


class MatchUpdate(BaseModel):
    player_character: str | None = Field(default=None, min_length=1, max_length=80)
    opponent_character: str | None = Field(default=None, min_length=1, max_length=80)
    result: Literal["win", "loss"] | None = None
    played_on: date | None = None
    rank_floor: str | None = Field(default=None, max_length=80)
    duration_seconds: int | None = Field(default=None, ge=1, le=MAX_DURATION_SECONDS)
    rounds_won: int | None = Field(default=None, ge=0, le=MAX_SET_SCORE)
    rounds_lost: int | None = Field(default=None, ge=0, le=MAX_SET_SCORE)
    first_to: int | None = Field(default=None, gt=0, le=MAX_SET_SCORE)
    notes: str | None = Field(default=None, max_length=2000)
    mistake_tags: list[str] | None = None
    strength_tags: list[str] | None = None
    reason_for_loss: str | None = Field(default=None, max_length=160)
    practice_next: str | None = Field(default=None, max_length=1000)
    replay_filename: str | None = Field(default=None, max_length=255)

    _validate_player_character = field_validator("player_character")(lambda value: validate_character(value) if value is not None else None)
    _validate_opponent_character = field_validator("opponent_character")(lambda value: validate_character(value) if value is not None else None)
    _validate_rank_floor = field_validator("rank_floor")(lambda value: validate_required_rank(value) if value is not None else None)
    _validate_played_on = field_validator("played_on")(lambda value: validate_played_on(value) if value is not None else None)
    _clean_notes = field_validator("notes")(clean_optional_text)
    _clean_reason_for_loss = field_validator("reason_for_loss")(clean_optional_text)
    _clean_practice_next = field_validator("practice_next")(clean_optional_text)
    _clean_replay_filename = field_validator("replay_filename")(clean_optional_text)
    _validate_mistake_tags = field_validator("mistake_tags")(validate_tags)
    _validate_strength_tags = field_validator("strength_tags")(validate_tags)

    @model_validator(mode="after")
    def reject_explicit_empty_rank(self) -> "MatchUpdate":
        if "rank_floor" in self.model_fields_set and self.rank_floor is None:
            raise ValueError("Select a rank.")
        return self


class MatchRead(BaseModel):
    id: int
    player_character: str
    opponent_character: str
    result: Literal["win", "loss"]
    played_on: date
    rank_floor: str | None = None
    duration_seconds: int | None = None
    rounds_won: int | None = None
    rounds_lost: int | None = None
    first_to: int | None = None
    notes: str | None = None
    mistake_tags: list[str] = Field(default_factory=list)
    strength_tags: list[str] = Field(default_factory=list)
    reason_for_loss: str | None = None
    practice_next: str | None = None
    replay_filename: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
