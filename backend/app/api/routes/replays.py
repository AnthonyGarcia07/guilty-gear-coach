from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Match, Replay, User
from app.schemas.replay import ReplayCreate, ReplayRead, ReplayUpdate

router = APIRouter(prefix="/matches/{match_id}/replays", tags=["replays"])


def get_owned_match(match_id: int, current_user: User, db: Session) -> Match:
    match = db.scalar(select(Match).where(Match.id == match_id, Match.owner_id == current_user.id))
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return match


def get_match_replay(match_id: int, replay_id: int, db: Session) -> Replay:
    replay = db.scalar(select(Replay).where(Replay.id == replay_id, Replay.match_id == match_id))
    if not replay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Replay not found")
    return replay


@router.get("", response_model=list[ReplayRead])
def list_replays(match_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Replay]:
    get_owned_match(match_id, current_user, db)
    return list(db.scalars(select(Replay).where(Replay.match_id == match_id).order_by(Replay.created_at.asc(), Replay.id.asc())))


@router.post("", response_model=ReplayRead, status_code=status.HTTP_201_CREATED)
def create_replay(match_id: int, payload: ReplayCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Replay:
    get_owned_match(match_id, current_user, db)
    replay = Replay(match_id=match_id, **payload.model_dump())
    db.add(replay)
    db.commit()
    db.refresh(replay)
    return replay


@router.get("/{replay_id}", response_model=ReplayRead)
def get_replay(match_id: int, replay_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Replay:
    get_owned_match(match_id, current_user, db)
    return get_match_replay(match_id, replay_id, db)


@router.patch("/{replay_id}", response_model=ReplayRead)
def update_replay(match_id: int, replay_id: int, payload: ReplayUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Replay:
    get_owned_match(match_id, current_user, db)
    replay = get_match_replay(match_id, replay_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(replay, field, value)
    replay.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(replay)
    return replay


@router.delete("/{replay_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_replay(match_id: int, replay_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    get_owned_match(match_id, current_user, db)
    replay = get_match_replay(match_id, replay_id, db)
    db.delete(replay)
    db.commit()
