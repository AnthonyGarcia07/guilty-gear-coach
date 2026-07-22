from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Match, User
from app.schemas.coaching import CoachingInsights
from app.services.coaching import build_coaching_insights

router = APIRouter(prefix="/coaching", tags=["coaching"])


@router.get("/insights", response_model=CoachingInsights)
def coaching_insights(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CoachingInsights:
    matches = list(db.scalars(select(Match).where(Match.owner_id == current_user.id).order_by(Match.played_on.asc(), Match.id.asc())))
    return build_coaching_insights(matches)
