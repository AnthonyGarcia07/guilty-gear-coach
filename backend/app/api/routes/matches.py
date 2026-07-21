from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Match, User
from app.schemas.match import MatchCreate, MatchRead, MatchUpdate

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[MatchRead])
def list_matches(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Match]:
    return list(db.scalars(select(Match).where(Match.owner_id == current_user.id).order_by(Match.updated_at.desc(), Match.id.desc())))


@router.post("", response_model=MatchRead, status_code=status.HTTP_201_CREATED)
def create_match(payload: MatchCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Match:
    match = Match(owner_id=current_user.id, **payload.model_dump())
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


@router.get("/{match_id}", response_model=MatchRead)
def get_match(match_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Match:
    match = db.get(Match, match_id)
    if not match or match.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return match


@router.patch("/{match_id}", response_model=MatchRead)
def update_match(match_id: int, payload: MatchUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Match:
    match = db.get(Match, match_id)
    if not match or match.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(match, field, value)
    match.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(match)
    return match


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_match(match_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    match = db.get(Match, match_id)
    if not match or match.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    db.delete(match)
    db.commit()
