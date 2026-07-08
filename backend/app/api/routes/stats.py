from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Match, User
from app.schemas.stats import DashboardStats
from app.services.stats import build_dashboard_stats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/dashboard", response_model=DashboardStats)
def dashboard_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DashboardStats:
    matches = list(db.scalars(select(Match).where(Match.owner_id == current_user.id).order_by(Match.played_on.desc(), Match.id.desc())))
    return build_dashboard_stats(matches)
