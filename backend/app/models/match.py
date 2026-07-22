from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    player_character: Mapped[str] = mapped_column(String(80), index=True)
    opponent_character: Mapped[str] = mapped_column(String(80), index=True)
    result: Mapped[str] = mapped_column(String(8), index=True)
    played_on: Mapped[date] = mapped_column(Date, index=True)
    rank_floor: Mapped[str | None] = mapped_column(String(80), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rounds_won: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rounds_lost: Mapped[int | None] = mapped_column(Integer, nullable=True)
    first_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    mistake_tags: Mapped[list[str]] = mapped_column(MutableList.as_mutable(ARRAY(String)), default=list)
    strength_tags: Mapped[list[str]] = mapped_column(MutableList.as_mutable(ARRAY(String)), default=list)
    reason_for_loss: Mapped[str | None] = mapped_column(String(160), nullable=True)
    practice_next: Mapped[str | None] = mapped_column(Text, nullable=True)
    replay_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="matches")
