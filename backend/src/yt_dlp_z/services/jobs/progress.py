"""Writes a running job's progress to the DB and to clients."""

import asyncio
import dataclasses
import logging
import time
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.job import Job
from yt_dlp_z.services.jobs.context import JobContext, publish_job
from yt_dlp_z.services.media_server.nfo import write_nfo_files
from yt_dlp_z.services.ytdlp.output import (
    FileUpdate,
    InfoUpdate,
    NfoUpdate,
    ProgressUpdate,
    Update,
    combine_parts,
)

logger = logging.getLogger(__name__)

PUBLISH_INTERVAL_SECONDS = 0.5
# Each recording part, and each retry through another proxy, starts its progress afresh.
PROGRESS_RESET = {"progress": None, "downloaded_bytes": None, "total_bytes": None, "speed": None}


def _changes_for(update: Update) -> dict[str, Any]:
    if isinstance(update, ProgressUpdate):
        changes = dataclasses.asdict(update)
        del changes["part"], changes["fragments"]
        return changes
    if isinstance(update, InfoUpdate):
        return {"title": update.title} if update.title else {}
    if isinstance(update, NfoUpdate):
        return {}
    return {"filepath": update.filepath}


class ProgressTracker:
    """Applies updates to the job, writing and publishing progress at most twice a second."""

    def __init__(self, context: JobContext, session: AsyncSession, job: Job) -> None:
        self._context = context
        self._session = session
        self._job = job
        self._last_flush = 0.0
        # Latest progress of each parallel stream (video and audio in recordings).
        self._parts: dict[int, ProgressUpdate] = {}

    async def apply(self, update: Update) -> None:
        if isinstance(update, NfoUpdate):
            await self._write_nfo(update)
            return
        if isinstance(update, ProgressUpdate):
            self._parts[update.part] = update
            update = combine_parts(self._parts)
        for name, value in _changes_for(update).items():
            setattr(self._job, name, value)
        due = time.monotonic() - self._last_flush >= PUBLISH_INTERVAL_SECONDS
        if due or isinstance(update, InfoUpdate | FileUpdate):
            await self.flush()

    async def _write_nfo(self, update: NfoUpdate) -> None:
        layout = self._job.media_layout
        if layout is None:
            return
        download_dir = Path(self._job.output_dir)
        try:
            await asyncio.to_thread(write_nfo_files, update.info, layout, download_dir)
        except OSError:
            # The video itself is saved; a missing .nfo shouldn't fail the download.
            logger.warning("Couldn't write the .nfo files for job %s", self._job.id, exc_info=True)

    async def flush(self) -> None:
        self._job.revision += 1
        await self._session.commit()
        publish_job(self._context.hub, self._job)
        self._last_flush = time.monotonic()
