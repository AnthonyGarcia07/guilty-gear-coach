"""Define how replay information is stored in PostgreSQL.

This model stores facts *about* a replay, such as its filename, upload status,
and inspected video details. It does not store the large MP4 file itself. The
MP4 lives in private cloud storage, and ``storage_key`` tells the backend where
to find it.

A replay does not have its own user ID. To check ownership, follow the
relationship from Replay to Match, then from Match to User. Keeping that path
consistent is important because every replay operation must be account-scoped.
"""

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Replay(Base):
    """Represent one replay record as a SQLAlchemy model.

    ``Mapped`` type hints describe the Python value for each column, while
    ``mapped_column`` describes how PostgreSQL should store that value.
    """

    __tablename__ = "replays"
    # Check constraints are a final safety net at the database level. Pydantic
    # catches bad API input earlier, but these rules also protect data written by
    # scripts, migrations, or future code that does not pass through the API.
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
    # A replay may be only a reference or filename, so not every record has an
    # uploaded video. ``source_type`` describes what kind of replay this is.
    source_type: Mapped[str] = mapped_column(String(32))
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ``storage_key`` is the video's private name inside the R2 bucket. It is not
    # a public URL and should not be used as proof that an upload succeeded.
    # ``upload_status`` records which step of the upload process has completed.
    storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True, unique=True, index=True)
    upload_status: Mapped[str] = mapped_column(String(32), default="metadata_only", server_default="metadata_only")
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Processing state is separate from upload state. A file can be uploaded but
    # not yet inspected. If inspection fails, ``processing_error`` contains a
    # short, safe message that may be shown to the user.
    processing_status: Mapped[str] = mapped_column(String(32), default="not_processed", server_default="not_processed")
    processing_error: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # These fields start empty. After ffprobe inspects a confirmed upload, the
    # backend saves the measured duration, dimensions, frame rate, and codec.
    metadata_inspected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    video_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    video_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    video_codec: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    match = relationship("Match", back_populates="replays")


""" I use a SQLAlchemy Replay model to store metadata about uploaded videos. 

Each replay is linked to a match through a foreign key, and the match belongs to a user. 
The actual MP4 is stored privately in Cloudflare R2, while PostgreSQL stores its object key, 
upload status, processing status, and inspected video metadata. 
This keeps large video files out of the relational database and lets the backend track their processing
"""