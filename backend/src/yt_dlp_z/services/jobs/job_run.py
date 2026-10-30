"""Runs a single download job: builds the command and streams progress to the DB and clients."""

import asyncio
import contextlib
import dataclasses
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from yt_dlp_z.core.config import Settings
from yt_dlp_z.db.models.job import Job, JobKind, JobStatus, utcnow
from yt_dlp_z.schemas.jobs import JobEvent, JobOut
from yt_dlp_z.services.cookies.store import cookie_path, working_copy
from yt_dlp_z.services.events import EventHub
from yt_dlp_z.services.jobs import repository
from yt_dlp_z.services.jobs.process import ProcessResult, run_ytdlp
from yt_dlp_z.services.ytdlp.args import build_user_args
from yt_dlp_z.services.ytdlp.command import build_command
from yt_dlp_z.services.ytdlp.errors import ArgumentError, SchemaUnavailableError
from yt_dlp_z.services.ytdlp.output import (
    FileUpdate,
    InfoUpdate,
    ProgressUpdate,
    Update,
    combine_parts,
)
from yt_dlp_z.services.ytdlp.schema import OptionSchemaProvider

PUBLISH_INTERVAL_SECONDS = 0.5
# Recordings start from the stream's beginning, and wait (retrying every 30 s to 5 min)
# when the stream starts later than announced.
LIVE_ARGS = ["--live-from-start", "--wait-for-video", "30-300"]


@dataclass(frozen=True)
class JobContext:
    session_factory: async_sessionmaker[AsyncSession]
    hub: EventHub
    settings: Settings
    schemas: OptionSchemaProvider


def publish_job(hub: EventHub, job: Job) -> None:
    hub.publish(JobEvent(job=JobOut.model_validate(job)).model_dump(mode="json"))


def job_log_path(settings: Settings, job_id: int) -> Path:
    return settings.config_dir / "logs" / f"job-{job_id}.log"


def _changes_for(update: Update) -> dict[str, Any]:
    if isinstance(update, ProgressUpdate):
        changes = dataclasses.asdict(update)
        del changes["part"]
        return changes
    if isinstance(update, InfoUpdate):
        return {"title": update.title} if update.title else {}
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
        if isinstance(update, ProgressUpdate):
            self._parts[update.part] = update
            update = combine_parts(self._parts)
        for name, value in _changes_for(update).items():
            setattr(self._job, name, value)
        due = time.monotonic() - self._last_flush >= PUBLISH_INTERVAL_SECONDS
        if due or isinstance(update, InfoUpdate | FileUpdate):
            await self.flush()

    async def flush(self) -> None:
        self._job.revision += 1
        await self._session.commit()
        publish_job(self._context.hub, self._job)
        self._last_flush = time.monotonic()


Outcome = tuple[JobStatus, str | None]


def _outcome(result: ProcessResult, cancelled: bool) -> Outcome:
    if cancelled:
        return JobStatus.CANCELLED, None
    if result.returncode == 0:
        return JobStatus.COMPLETED, None
    return JobStatus.FAILED, result.error or f"yt-dlp exited with code {result.returncode}."


async def _finish(context: JobContext, session: AsyncSession, job: Job, outcome: Outcome) -> None:
    status, error = outcome
    await repository.save(
        session, job, status=status, error=error, speed=None, eta=None, finished_at=utcnow()
    )
    publish_job(context.hub, job)


class MissingCookiesError(Exception):
    pass


@contextlib.contextmanager
def _cookie_args(settings: Settings, job: Job) -> Iterator[list[str]]:
    if job.cookie_id is None:
        yield []
        return
    if not cookie_path(settings.config_dir, job.cookie_id).exists():
        raise MissingCookiesError(
            "The cookies file for this download was deleted. Start it again with another one."
        )
    with working_copy(settings.config_dir, job.cookie_id, f"job-{job.id}") as path:
        yield ["--cookies", str(path)]


async def _command_for(context: JobContext, job: Job, cookie_args: list[str]) -> list[str]:
    _, index = await context.schemas.get()
    allow_unsafe = context.settings.allow_unsafe_options
    user_args = build_user_args(index, job.options, job.extra_args, allow_unsafe=allow_unsafe)
    user_args += cookie_args
    if job.kind == JobKind.LIVE:
        user_args = [*LIVE_ARGS, *user_args]
    return build_command(context.settings.ytdlp_command, user_args, job.url, Path(job.output_dir))


async def execute_job(
    context: JobContext,
    job_id: int,
    on_start: Callable[[asyncio.subprocess.Process], None],
    is_cancelled: Callable[[], bool],
) -> None:
    async with context.session_factory() as session:
        job = await repository.get_job(session, job_id)
        if job is None or job.status != JobStatus.QUEUED:
            return
        # Holds the job's temporary cookies copy until yt-dlp exits.
        with contextlib.ExitStack() as cleanup:
            try:
                cookie_args = cleanup.enter_context(_cookie_args(context.settings, job))
                command = await _command_for(context, job, cookie_args)
            except (ArgumentError, SchemaUnavailableError, MissingCookiesError) as error:
                await _finish(context, session, job, (JobStatus.FAILED, str(error)))
                return
            await repository.save(session, job, status=JobStatus.RUNNING, started_at=utcnow())
            publish_job(context.hub, job)

            tracker = ProgressTracker(context, session, job)
            log_path = job_log_path(context.settings, job_id)
            result = await run_ytdlp(command, log_path, tracker.apply, on_start)
            await _finish(context, session, job, _outcome(result, is_cancelled()))
