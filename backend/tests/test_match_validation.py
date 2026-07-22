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
        "rounds_won": 2,
        "rounds_lost": 1,
        "first_to": 2,
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
    assert match.rounds_won == 2
    assert match.rounds_lost == 1
    assert match.first_to == 2
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
        ("rounds_won", -1, "greater than or equal to 0"),
        ("rounds_lost", -1, "greater than or equal to 0"),
        ("rounds_won", 2323, "less than or equal to 10"),
        ("first_to", 0, "greater than 0"),
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


@pytest.mark.parametrize(
    ("result", "rounds_won", "rounds_lost", "first_to"),
    [
        ("win", 2, 0, 2),
        ("win", 2, 1, 2),
        ("loss", 0, 2, 2),
        ("loss", 1, 2, 2),
        ("win", 3, 2, 3),
        ("loss", 1, 3, 3),
    ],
)
def test_match_create_accepts_realistic_completed_set_scores(result: str, rounds_won: int, rounds_lost: int, first_to: int):
    payload = valid_match_payload()
    payload.update({"result": result, "rounds_won": rounds_won, "rounds_lost": rounds_lost, "first_to": first_to})

    match = MatchCreate(**payload)

    assert match.rounds_won == rounds_won
    assert match.rounds_lost == rounds_lost
    assert match.first_to == first_to


@pytest.mark.parametrize(
    ("result", "rounds_won", "rounds_lost", "first_to", "message"),
    [
        ("win", 1, 1, 2, "cannot be tied"),
        ("loss", 2, 2, 3, "cannot be tied"),
        ("win", 1, 2, 2, "win must have your score ahead"),
        ("loss", 2, 1, 2, "loss must have the opponent score ahead"),
        ("win", 1, 0, 2, "exactly one side reaching"),
        ("win", 2, 2, 2, "cannot be tied"),
    ],
)
def test_match_create_rejects_inconsistent_completed_set_scores(result: str, rounds_won: int, rounds_lost: int, first_to: int, message: str):
    payload = valid_match_payload()
    payload.update({"result": result, "rounds_won": rounds_won, "rounds_lost": rounds_lost, "first_to": first_to})

    with pytest.raises(ValidationError) as error:
        MatchCreate(**payload)

    assert message in str(error.value)


def test_match_create_requires_complete_score_context_when_score_is_present():
    payload = valid_match_payload()
    payload["first_to"] = None

    with pytest.raises(ValidationError) as error:
        MatchCreate(**payload)

    assert "Enter rounds won, rounds lost, and first-to together" in str(error.value)


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
