"""Runs a single download job: builds the command and streams progress to the DB and clients."""

import asyncio
import contextlib
import dataclasses
import logging
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
from yt_dlp_z.services.jobs.process import ProcessHooks, ProcessResult, run_ytdlp
from yt_dlp_z.services.live.recorder import (
    Outcome,
    PartWatch,
    RecordingHooks,
    part_args,
    record,
)
from yt_dlp_z.services.media_server.layout import job_media_args
from yt_dlp_z.services.media_server.nfo import write_nfo_files
from yt_dlp_z.services.ytdlp.args import build_user_args
from yt_dlp_z.services.ytdlp.command import build_command
from yt_dlp_z.services.ytdlp.errors import ArgumentError, SchemaUnavailableError
from yt_dlp_z.services.ytdlp.output import (
    FileUpdate,
    InfoUpdate,
    NfoUpdate,
    ProgressUpdate,
    Update,
    combine_parts,
)
from yt_dlp_z.services.ytdlp.schema import OptionSchemaProvider

logger = logging.getLogger(__name__)

PUBLISH_INTERVAL_SECONDS = 0.5
# Each recording part starts its progress afresh.
PART_RESET = {"progress": None, "downloaded_bytes": None, "total_bytes": None, "speed": None}


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


async def _command_for(
    context: JobContext, job: Job, cookie_args: list[str], app_args: list[str]
) -> list[str]:
    """`app_args`: options yt-dlp-z adds itself (recordings), after the user's own."""
    _, index = await context.schemas.get()
    allow_unsafe = context.settings.allow_unsafe_options
    user_args = build_user_args(index, job.options, job.extra_args, allow_unsafe=allow_unsafe)
    user_args += [*cookie_args, *app_args]
    return build_command(context.settings.ytdlp_command, user_args, job.url, Path(job.output_dir))


@dataclass(frozen=True)
class RunControl:
    on_start: Callable[[asyncio.subprocess.Process], None]
    is_cancelled: Callable[[], bool]


@dataclass(frozen=True)
class Running:
    """The job being run, with what running it needs."""

    context: JobContext
    session: AsyncSession
    job: Job
    control: RunControl


def _first_app_args(job: Job) -> list[str]:
    if job.kind == JobKind.LIVE:
        return [*job_media_args(job), *part_args(job, (job.part or 0) + 1)]
    return job_media_args(job)


async def _record(running: Running, cookie_args: list[str]) -> Outcome:
    context, session, job = running.context, running.session, running.job
    log_path = job_log_path(context.settings, job.id)

    async def run_part(app_args: list[str], watch: PartWatch) -> ProcessResult:
        command = await _command_for(context, job, cookie_args, [*job_media_args(job), *app_args])
        tracker = ProgressTracker(context, session, job)

        async def on_update(update: Update) -> None:
            if isinstance(update, ProgressUpdate):
                watch.on_progress(update)
            await tracker.apply(update)

        hooks = ProcessHooks(on_update, watch.on_start, graceful=True)
        return await run_ytdlp(command, log_path, hooks)

    async def on_part(part: int) -> None:
        await repository.save(session, job, part=part, **PART_RESET)
        publish_job(context.hub, job)

    control = running.control
    return await record(
        job, RecordingHooks(run_part, control.on_start, control.is_cancelled, on_part)
    )


async def _download(running: Running, command: list[str]) -> Outcome:
    tracker = ProgressTracker(running.context, running.session, running.job)
    log_path = job_log_path(running.context.settings, running.job.id)
    result = await run_ytdlp(
        command, log_path, ProcessHooks(tracker.apply, running.control.on_start)
    )
    return _outcome(result, running.control.is_cancelled())


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
        running = Running(context, session, job, RunControl(on_start, is_cancelled))
        # Holds the job's temporary cookies copy until yt-dlp exits.
        with contextlib.ExitStack() as cleanup:
            try:
                cookie_args = cleanup.enter_context(_cookie_args(context.settings, job))
                # Built up front for downloads, and to catch bad options before starting.
                command = await _command_for(context, job, cookie_args, _first_app_args(job))
            except (ArgumentError, SchemaUnavailableError, MissingCookiesError) as error:
                await _finish(context, session, job, (JobStatus.FAILED, str(error)))
                return
            await repository.save(session, job, status=JobStatus.RUNNING, started_at=utcnow())
            publish_job(context.hub, job)
            if job.kind == JobKind.LIVE:
                outcome = await _record(running, cookie_args)
            else:
                outcome = await _download(running, command)
            await _finish(context, session, job, outcome)
