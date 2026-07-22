from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.routes.matches import create_match, update_match
from app.models import Match
from app.schemas.match import MatchCreate, MatchUpdate


class FakeDb:
    def __init__(self, match: Match | None = None):
        self.match = match
        self.added = None
        self.commits = 0

    def add(self, match: Match) -> None:
        self.added = match
        self.match = match

    def commit(self) -> None:
        self.commits += 1

    def refresh(self, match: Match) -> None:
        self.match = match

    def get(self, model, match_id: int):
        if model is Match and self.match and self.match.id == match_id:
            return self.match
        return None


def match_payload() -> dict:
    return {
        "player_character": "Sol Badguy",
        "opponent_character": "Ky Kiske",
        "result": "win",
        "played_on": date(2026, 7, 1),
        "rank_floor": "Iron",
        "duration_seconds": 180,
        "rounds_won": 2,
        "rounds_lost": 1,
        "first_to": 2,
        "notes": "Round count tracked.",
        "mistake_tags": [],
        "strength_tags": [],
        "reason_for_loss": None,
        "practice_next": None,
        "replay_filename": None,
    }


def test_create_match_persists_coaching_fields():
    db = FakeDb()
    current_user = SimpleNamespace(id=7)

    match = create_match(MatchCreate(**match_payload()), current_user=current_user, db=db)

    assert db.added is match
    assert db.commits == 1
    assert match.owner_id == 7
    assert match.rounds_won == 2
    assert match.rounds_lost == 1
    assert match.first_to == 2
    assert match.notes == "Round count tracked."


def test_update_match_persists_coaching_fields():
    match = Match(id=11, owner_id=7, **match_payload())
    db = FakeDb(match)
    current_user = SimpleNamespace(id=7)

    updated = update_match(
        11,
        MatchUpdate(rounds_won=3, rounds_lost=2, first_to=3, notes="Updated coaching notes."),
        current_user=current_user,
        db=db,
    )

    assert updated.rounds_won == 3
    assert updated.rounds_lost == 2
    assert updated.first_to == 3
    assert updated.notes == "Updated coaching notes."
    assert db.commits == 1


def test_update_match_rejects_score_inconsistent_with_result():
    match = Match(id=11, owner_id=7, **match_payload())
    db = FakeDb(match)
    current_user = SimpleNamespace(id=7)

    with pytest.raises(HTTPException) as error:
        update_match(
            11,
            MatchUpdate(rounds_won=1, rounds_lost=2, first_to=2),
            current_user=current_user,
            db=db,
        )

    assert error.value.status_code == 422
    assert "win must have your score ahead" in str(error.value.detail)
