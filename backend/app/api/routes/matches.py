from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Match, User
from app.schemas.match import MatchCreate, MatchListResponse, MatchRead, MatchUpdate, validate_completed_set_score
from app.services.match_history import (
    DEFAULT_MATCH_PAGE,
    DEFAULT_MATCH_PAGE_SIZE,
    DEFAULT_MATCH_SORT,
    MAX_MATCH_PAGE_SIZE,
    MatchSort,
    apply_match_history_sort,
    offset_for_page,
    total_pages,
)

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=MatchListResponse)
def list_matches(
    page: Annotated[int, Query(ge=1)] = DEFAULT_MATCH_PAGE,
    page_size: Annotated[int, Query(ge=1, le=MAX_MATCH_PAGE_SIZE)] = DEFAULT_MATCH_PAGE_SIZE,
    sort: MatchSort = DEFAULT_MATCH_SORT,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MatchListResponse:
    owner_filter = Match.owner_id == current_user.id
    total_items = db.scalar(select(func.count()).select_from(Match).where(owner_filter)) or 0
    pages = total_pages(total_items, page_size)
    requested_page = min(page, pages)
    statement = apply_match_history_sort(select(Match).where(owner_filter), sort).offset(offset_for_page(requested_page, page_size)).limit(page_size)
    return MatchListResponse(
        items=list(db.scalars(statement)),
        page=requested_page,
        page_size=page_size,
        total_items=total_items,
        total_pages=pages,
        sort=sort,
    )


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
    updates = payload.model_dump(exclude_unset=True)
    result = updates.get("result", match.result)
    rounds_won = updates.get("rounds_won", match.rounds_won)
    rounds_lost = updates.get("rounds_lost", match.rounds_lost)
    first_to = updates.get("first_to", match.first_to)
    try:
        validate_completed_set_score(result, rounds_won, rounds_lost, first_to)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[{"loc": ["body", "rounds_won"], "msg": str(error), "type": "value_error"}],
        ) from error
    for field, value in updates.items():
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
