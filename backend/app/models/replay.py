from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Replay(Base):
    __tablename__ = "replays"
    __table_args__ = (
        CheckConstraint("source_type IN ('replay_file', 'video', 'external_reference')", name="ck_replays_source_type"),
        CheckConstraint("upload_status IN ('metadata_only', 'pending_upload', 'uploaded')", name="ck_replays_upload_status"),
        CheckConstraint("size_bytes IS NULL OR size_bytes >= 0", name="ck_replays_size_bytes_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), index=True)
    source_type: Mapped[str] = mapped_column(String(32))
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True, unique=True, index=True)
    upload_status: Mapped[str] = mapped_column(String(32), default="metadata_only", server_default="metadata_only")
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    match = relationship("Match", back_populates="replays")
