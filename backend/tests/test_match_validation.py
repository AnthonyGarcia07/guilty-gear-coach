from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.match import MatchCreate, MatchRead, MatchUpdate


def valid_match_payload() -> dict:
    return {
        "player_character": "Sol Badguy",
        "opponent_character": "Queen Dizzy",
        "result": "win",
        "played_on": date(2026, 7, 1),
        "rank_floor": " Diamond ",
        "duration_seconds": 180,
        "notes": "  Good anti-air conversions.  ",
        "mistake_tags": [" meter spend ", "meter spend", "corner escape"],
        "strength_tags": [" whiff punish "],
        "reason_for_loss": "  ",
        "practice_next": "  Lab corner escape routes. ",
        "replay_filename": "  set-01.mp4 ",
    }


def test_match_create_trims_optional_text_and_tags():
    match = MatchCreate(**valid_match_payload())

    assert match.rank_floor == "Diamond"
    assert match.notes == "Good anti-air conversions."
    assert match.mistake_tags == ["meter spend", "corner escape"]
    assert match.reason_for_loss is None
    assert match.practice_next == "Lab corner escape routes."
    assert match.replay_filename == "set-01.mp4"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("player_character", "Order-Sol", "supported Guilty Gear Strive character"),
        ("rank_floor", "Floor 10", "valid Guilty Gear Strive rank"),
        ("rank_floor", "Celestial Challenge", "valid Guilty Gear Strive rank"),
        ("duration_seconds", 1801, "less than or equal to 1800"),
        ("duration_seconds", -1, "greater than or equal to 1"),
        ("played_on", date(2021, 6, 10), "June 11, 2021"),
        ("played_on", date.today() + timedelta(days=1), "future"),
        ("notes", "x" * 2001, "at most 2000"),
        ("reason_for_loss", "x" * 161, "at most 160"),
        ("practice_next", "x" * 1001, "at most 1000"),
    ],
)
def test_match_create_rejects_invalid_values(field: str, value, message: str):
    payload = valid_match_payload()
    payload[field] = value

    with pytest.raises(ValidationError) as error:
        MatchCreate(**payload)

    assert message in str(error.value)


def test_match_update_uses_same_validation_rules():
    with pytest.raises(ValidationError) as error:
        MatchUpdate(rank_floor="Floor 10", played_on=date.today() + timedelta(days=1))

    message = str(error.value)
    assert "valid Guilty Gear Strive rank" in message
    assert "future" in message


def test_match_update_can_omit_rank_but_rejects_explicit_empty_rank():
    assert MatchUpdate(practice_next="Lab defense").rank_floor is None

    with pytest.raises(ValidationError) as error:
        MatchUpdate(rank_floor=None)

    assert "Select a rank" in str(error.value)


def test_match_read_allows_legacy_rank_values():
    payload = valid_match_payload()
    payload["rank_floor"] = "Floor 10"
    payload["id"] = 1
    payload["created_at"] = date(2026, 7, 1)
    payload["updated_at"] = date(2026, 7, 1)

    match = MatchRead(**payload)

    assert match.rank_floor == "Floor 10"
