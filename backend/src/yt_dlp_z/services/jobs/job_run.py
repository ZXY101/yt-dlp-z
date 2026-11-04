"""Runs a single job: builds the yt-dlp command, picks its proxy and saves the outcome."""

import asyncio
import contextlib
import logging
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.core.config import Settings
from yt_dlp_z.db.models.job import Job, JobKind, JobStatus, utcnow
from yt_dlp_z.services.cookies.store import cookie_path, working_copy
from yt_dlp_z.services.jobs import repository
from yt_dlp_z.services.jobs.context import JobContext, RunControl, job_log_path, publish_job
from yt_dlp_z.services.jobs.job_proxy import cool_down_if_blocked, hide_proxy_password, use_proxy
from yt_dlp_z.services.jobs.process import ProcessHooks, ProcessResult, run_ytdlp
from yt_dlp_z.services.jobs.progress import PROGRESS_RESET, ProgressTracker
from yt_dlp_z.services.live.recorder import (
    Outcome,
    PartWatch,
    RecordingHooks,
    number_first_part,
    part_args,
    record,
)
from yt_dlp_z.services.live.vod import after_finish, vod_args
from yt_dlp_z.services.live_chat.capture import NoCapture, capture_for
from yt_dlp_z.services.live_chat.job_step import ChatRun, chat_print_args, run_chat_step
from yt_dlp_z.services.media_server.layout import job_media_args
from yt_dlp_z.services.proxies.pool import NoProxyError
from yt_dlp_z.services.proxies.store import get_proxy
from yt_dlp_z.services.ytdlp.args import build_user_args
from yt_dlp_z.services.ytdlp.command import build_command
from yt_dlp_z.services.ytdlp.errors import ArgumentError, SchemaUnavailableError
from yt_dlp_z.services.ytdlp.json_run import YtdlpJsonError, run_ytdlp_json
from yt_dlp_z.services.ytdlp.output import ChatUpdate, FileUpdate, ProgressUpdate, Update

# Proxies a download tries before giving up. Each one YouTube blocks goes on cooldown.
logger = logging.getLogger(__name__)
MAX_PROXY_ATTEMPTS = 3
SECOND_PART = 2


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
    try:
        await after_finish(context, session, job)
    except Exception:
        # The job itself is done; a VOD that couldn't be scheduled is only logged.
        logger.exception("Follow-up of job %s failed", job.id)


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
    context: JobContext, job: Job, access_args: list[str], app_args: list[str]
) -> list[str]:
    """`access_args`: --cookies and --proxy. `app_args`: other options yt-dlp-z adds
    itself (recordings, media-server output). Both go after the user's own options."""
    _, index = await context.schemas.get()
    allow_unsafe = context.settings.allow_unsafe_options
    user_args = build_user_args(index, job.options, job.extra_args, allow_unsafe=allow_unsafe)
    user_args += [*access_args, *app_args]
    return build_command(context.settings.ytdlp_command, user_args, job.url, Path(job.output_dir))


@dataclass(frozen=True)
class Running:
    """The job being run, with what running it needs."""

    context: JobContext
    session: AsyncSession
    job: Job
    control: RunControl
    # --cookies for the job's cookies file, if it has one.
    cookie_args: list[str]
    # The videos saved, for fetching their live chat afterwards.
    chat_videos: list[ChatUpdate] = field(default_factory=list)


def _first_app_args(job: Job) -> list[str]:
    if job.kind == JobKind.LIVE:
        return [*job_media_args(job), *part_args(job, (job.part or 0) + 1)]
    return [*job_media_args(job), *vod_args(job), *chat_print_args(job)]


async def _record_with_chat(
    running: Running, capture: NoCapture, hooks: RecordingHooks, proxy_args: list[str]
) -> Outcome:
    capture.start(proxy_args)
    try:
        outcome = await record(running.job, hooks)
    finally:
        await capture.stop()
    await capture.finish(running.session)
    return outcome


async def _record(running: Running, proxy_args: list[str]) -> Outcome:
    """Records the stream. A blocked proxy cools down, but the recording isn't retried."""
    context, session, job = running.context, running.session, running.job
    log_path = job_log_path(context.settings, job.id)
    access_args = [*running.cookie_args, *proxy_args]
    capture = capture_for(context, job)

    async def run_part(app_args: list[str], watch: PartWatch) -> ProcessResult:
        command = await _command_for(context, job, access_args, [*job_media_args(job), *app_args])
        tracker = ProgressTracker(context, session, job)

        async def on_update(update: Update) -> None:
            if isinstance(update, ProgressUpdate):
                watch.on_progress(update)
            if isinstance(update, FileUpdate):
                watch.on_file()
            capture.on_update(job.part or 1, update)
            await tracker.apply(update)

        hooks = ProcessHooks(on_update, watch.on_start, graceful=True)
        return await run_ytdlp(command, log_path, hooks)

    async def on_part(part: int) -> None:
        fields: dict[str, object] = {}
        # The recording became several files: the first one gets its part number too.
        if part == SECOND_PART and job.filepath:
            renamed = number_first_part(job.filepath)
            fields["filepath"] = renamed
            fields["files"] = [renamed if file == job.filepath else file for file in job.files]
            capture.renamed(job.filepath, renamed)
        capture.begin_part(part)
        await repository.save(session, job, part=part, **PROGRESS_RESET, **fields)
        publish_job(context.hub, job)

    async def still_live() -> bool:
        args = ["--no-playlist", *access_args]
        try:
            data = await run_ytdlp_json(context.settings.ytdlp_command, args, job.url)
        except YtdlpJsonError:
            return False
        live = data.get("live_status") == "is_live"
        if live:
            with log_path.open("a", encoding="utf-8") as log:
                log.write(
                    "[yt-dlp-z] The stream's links expired but it is still live; "
                    "continuing in the next part.\n"
                )
        return live

    control = running.control
    hooks = RecordingHooks(run_part, control.on_start, control.is_cancelled, on_part, still_live)
    outcome = await _record_with_chat(running, capture, hooks, proxy_args)
    await cool_down_if_blocked(session, job, outcome)
    return outcome


async def _download_once(running: Running, proxy_args: list[str]) -> Outcome:
    access_args = [*running.cookie_args, *proxy_args]
    job = running.job
    command = await _command_for(running.context, job, access_args, _first_app_args(job))
    tracker = ProgressTracker(running.context, running.session, job)
    log_path = job_log_path(running.context.settings, job.id)
    result = await run_ytdlp(
        command, log_path, ProcessHooks(tracker.apply, running.control.on_start)
    )
    running.chat_videos.extend(tracker.chat_videos)
    return _outcome(result, running.control.is_cancelled())


async def _download(running: Running, proxy_args: list[str]) -> Outcome:
    """Downloads. A proxy that YouTube blocks or that doesn't connect cools down, and
    the next one tries."""
    session, job = running.session, running.job
    tried: set[int] = set()
    while True:
        outcome = await _download_once(running, proxy_args)
        if not await cool_down_if_blocked(session, job, outcome) or job.proxy_id is None:
            return outcome
        tried.add(job.proxy_id)
        if len(tried) >= MAX_PROXY_ATTEMPTS:
            return outcome
        try:
            proxy_args = await use_proxy(running.context.proxies, session, job, tried)
        except NoProxyError as error:
            return JobStatus.FAILED, str(error)
        with job_log_path(running.context.settings, job.id).open("a", encoding="utf-8") as log:
            log.write("[yt-dlp-z] The proxy was blocked or didn't connect; trying the next one.\n")
        await repository.save(session, job, **PROGRESS_RESET)
        publish_job(running.context.hub, job)


async def _fetch_chat(running: Running) -> None:
    """After the video, on its own: a chat that fails must never fail the download."""
    job = running.job
    proxy = await get_proxy(running.session, job.proxy_id) if job.proxy_id is not None else None
    access_args = [*running.cookie_args, *(["--proxy", proxy.url] if proxy else [])]
    await run_chat_step(
        ChatRun(
            running.context,
            running.session,
            job,
            running.chat_videos,
            access_args,
            running.control,
        )
    )


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
                control = RunControl(on_start, is_cancelled)
                running = Running(context, session, job, control, cookie_args)
                proxy_args = await use_proxy(context.proxies, session, job, set())
                # Catches bad options before starting.
                await _command_for(context, job, [], _first_app_args(job))
            except (
                ArgumentError,
                SchemaUnavailableError,
                MissingCookiesError,
                NoProxyError,
            ) as error:
                await _finish(context, session, job, (JobStatus.FAILED, str(error)))
                return
            await repository.save(session, job, status=JobStatus.RUNNING, started_at=utcnow())
            publish_job(context.hub, job)
            if job.kind == JobKind.LIVE:
                outcome = await _record(running, proxy_args)
            else:
                outcome = await _download(running, proxy_args)
                if outcome[0] != JobStatus.CANCELLED:
                    await _fetch_chat(running)
            await _finish(context, session, job, await hide_proxy_password(session, job, outcome))
