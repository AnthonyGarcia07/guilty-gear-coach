from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Replay(Base):
    __tablename__ = "replays"
    __table_args__ = (
        CheckConstraint("source_type IN ('replay_file', 'video', 'external_reference')", name="ck_replays_source_type"),
        CheckConstraint("upload_status IN ('metadata_only', 'pending_upload', 'uploaded')", name="ck_replays_upload_status"),
        CheckConstraint("processing_status IN ('not_processed', 'processing', 'processed', 'failed')", name="ck_replays_processing_status"),
        CheckConstraint("size_bytes IS NULL OR size_bytes >= 0", name="ck_replays_size_bytes_non_negative"),
        CheckConstraint("video_duration_seconds IS NULL OR video_duration_seconds >= 0", name="ck_replays_video_duration_seconds_non_negative"),
        CheckConstraint("video_width IS NULL OR video_width > 0", name="ck_replays_video_width_positive"),
        CheckConstraint("video_height IS NULL OR video_height > 0", name="ck_replays_video_height_positive"),
        CheckConstraint("video_fps IS NULL OR video_fps > 0", name="ck_replays_video_fps_positive"),
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
    processing_status: Mapped[str] = mapped_column(String(32), default="not_processed", server_default="not_processed")
    processing_error: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_inspected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    video_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    video_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    video_codec: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    match = relationship("Match", back_populates="replays")
