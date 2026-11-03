from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from yt_dlp_z.db.base import Base
from yt_dlp_z.schemas.common import FileNaming, FolderLayout, ProxyMode


class JobStatus(StrEnum):
    SCHEDULED = "scheduled"  # a recording waiting for its stream (see services/live)
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobKind(StrEnum):
    DOWNLOAD = "download"
    # Records a live or upcoming stream from its start. Runs in its own queue.
    LIVE = "live"


FINISHED_STATUSES = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}


def utcnow() -> datetime:
    return datetime.now(UTC)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(Text)
    status: Mapped[JobStatus] = mapped_column(String(20), index=True)
    kind: Mapped[JobKind] = mapped_column(
        String(20), default=JobKind.DOWNLOAD, server_default=JobKind.DOWNLOAD.value
    )
    # When a scheduled recording's stream starts; the live scheduler queues it shortly before.
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    # Recording settings, copied from Settings when the job is created (see services/live).
    record_from_start: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    part_seconds: Mapped[int | None] = mapped_column(Integer, default=None)
    max_seconds: Mapped[int | None] = mapped_column(Integer, default=None)
    # The part being recorded (1, 2, …) when recordings are split into several files.
    part: Mapped[int | None] = mapped_column(Integer, default=None)
    options: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    extra_args: Mapped[str] = mapped_column(Text, default="")
    # No foreign key: a deleted cookies file must not delete history. Checked when used.
    cookie_id: Mapped[int | None] = mapped_column(Integer, default=None)
    # Set for downloads queued by a channel subscription (no foreign key, like cookie_id).
    subscription_id: Mapped[int | None] = mapped_column(Integer, default=None, index=True)
    output_dir: Mapped[str] = mapped_column(Text)
    # Media-server output (services/media_server), copied from the preset; None: off.
    # Layout: schemas/common.py FolderLayout and FileNaming, None for the plain default.
    folders: Mapped[FolderLayout | None] = mapped_column(String(20), default=None)
    file_name: Mapped[FileNaming | None] = mapped_column(String(20), default=None)
    media_files: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    # Copied from the preset. The proxy is picked when the job starts and kept for all of
    # it: switching mid-download breaks recordings (services/proxies).
    proxy_mode: Mapped[ProxyMode] = mapped_column(String(20), default="off", server_default="off")
    proxy_id: Mapped[int | None] = mapped_column(Integer, default=None)
    title: Mapped[str | None] = mapped_column(Text, default=None)
    progress: Mapped[float | None] = mapped_column(Float, default=None)
    downloaded_bytes: Mapped[int | None] = mapped_column(Integer, default=None)
    total_bytes: Mapped[int | None] = mapped_column(Integer, default=None)
    speed: Mapped[float | None] = mapped_column(Float, default=None)
    eta: Mapped[int | None] = mapped_column(Integer, default=None)
    filepath: Mapped[str | None] = mapped_column(Text, default=None)
    # Every file yt-dlp saved (playlists and recording parts give several). Files saved
    # beside them with the same name (.nfo, thumbnail, subtitles) are found from these.
    files: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")
    # Pinned by the user: never deleted by the subscription's "delete after N days".
    keep: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    # Recordings: download the VOD this long after the stream ends (None: don't), and
    # delete the recording once the VOD is saved. Copied from the live preset.
    vod_after_seconds: Mapped[int | None] = mapped_column(Integer, default=None)
    vod_replace: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    # A VOD download: the recording it follows (no foreign key, like cookie_id).
    source_job_id: Mapped[int | None] = mapped_column(Integer, default=None)
    error: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    # Bumped on every save, so clients can drop updates older than what they have.
    # (HTTP responses and WebSocket events for the same job can arrive out of order.)
    revision: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
