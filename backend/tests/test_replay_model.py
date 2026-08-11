from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Match, Replay, User


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def create_user(db: Session) -> User:
    suffix = uuid4().hex
    user = User(
        email=f"replay-{suffix}@example.com",
        username=f"replay_{suffix}",
        password_hash="not-a-real-password",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_match(db: Session, user: User, replay_filename: str | None = None) -> Match:
    match = Match(
        owner_id=user.id,
        player_character="Sol Badguy",
        opponent_character="Ky Kiske",
        result="win",
        played_on=date(2026, 7, 1),
        rank_floor="Gold",
        duration_seconds=180,
        rounds_won=2,
        rounds_lost=1,
        first_to=2,
        notes="Replay model test match.",
        mistake_tags=[],
        strength_tags=[],
        reason_for_loss=None,
        practice_next=None,
        replay_filename=replay_filename,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


def test_match_can_exist_with_no_replays(db: Session):
    user = create_user(db)
    match = create_match(db, user)

    assert match.replays == []

    db.delete(user)
    db.commit()


def test_replay_relationships_link_match_and_replay(db: Session):
    user = create_user(db)
    match = create_match(db, user)
    replay = Replay(match_id=match.id, source_type="replay_file", original_filename="set-vs-ky.rep")

    db.add(replay)
    db.commit()
    db.refresh(replay)
    db.refresh(match)

    assert replay.match_id == match.id
    assert replay.match.id == match.id
    assert [item.id for item in match.replays] == [replay.id]

    db.delete(user)
    db.commit()


def test_match_can_have_multiple_replays(db: Session):
    user = create_user(db)
    match = create_match(db, user)
    replays = [
        Replay(match_id=match.id, source_type="replay_file", original_filename="game-one.rep"),
        Replay(match_id=match.id, source_type="video", original_filename="game-two.mp4"),
    ]

    db.add_all(replays)
    db.commit()
    db.refresh(match)

    replay_match_ids = {replay.match_id for replay in match.replays}

    assert len(match.replays) == 2
    assert replay_match_ids == {match.id}

    db.delete(user)
    db.commit()


@pytest.mark.parametrize("source_type", ["replay_file", "video", "external_reference"])
def test_supported_source_types_can_be_stored(db: Session, source_type: str):
    user = create_user(db)
    match = create_match(db, user)
    replay = Replay(match_id=match.id, source_type=source_type, original_filename=None)

    db.add(replay)
    db.commit()
    db.refresh(replay)

    assert replay.source_type == source_type

    db.delete(user)
    db.commit()


def test_original_filename_is_nullable(db: Session):
    user = create_user(db)
    match = create_match(db, user)
    replay = Replay(match_id=match.id, source_type="external_reference", original_filename=None)

    db.add(replay)
    db.commit()
    db.refresh(replay)

    assert replay.original_filename is None

    db.delete(user)
    db.commit()


def test_deleting_match_cascades_to_replays(db: Session):
    user = create_user(db)
    match = create_match(db, user)
    replays = [
        Replay(match_id=match.id, source_type="replay_file", original_filename="one.rep"),
        Replay(match_id=match.id, source_type="video", original_filename="two.mp4"),
    ]
    db.add_all(replays)
    db.commit()
    replay_ids = [replay.id for replay in replays]
    match_id = match.id

    db.expire_all()
    match_to_delete = db.get(Match, match_id)
    assert match_to_delete is not None
    db.delete(match_to_delete)
    db.commit()

    assert db.get(Match, match_id) is None
    assert db.scalars(select(Replay).where(Replay.id.in_(replay_ids))).all() == []

    db.delete(user)
    db.commit()


def test_match_deletion_without_replays_still_works(db: Session):
    user = create_user(db)
    match = create_match(db, user)
    match_id = match.id

    db.delete(match)
    db.commit()

    assert db.get(Match, match_id) is None

    db.delete(user)
    db.commit()


def test_existing_match_fields_and_replay_filename_still_work(db: Session):
    user = create_user(db)
    match = create_match(db, user, replay_filename="legacy-placeholder.rep")

    stored_match = db.get(Match, match.id)

    assert stored_match is not None
    assert stored_match.owner_id == user.id
    assert stored_match.player_character == "Sol Badguy"
    assert stored_match.replay_filename == "legacy-placeholder.rep"

    db.delete(user)
    db.commit()
