"""A job's live chat: fetched with its own yt-dlp run once the video is saved.

Not part of the video's run, because yt-dlp fetches subtitles first: a slow or failing chat
would hold up or fail the video. Its output goes to the job's log and never changes the job's
outcome; job.chat_status says how it went.
"""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.job import Job, JobKind
from yt_dlp_z.schemas.live_chat import ChatStatus, LiveChatSettings, OverlayStyle
from yt_dlp_z.services.jobs import repository
from yt_dlp_z.services.jobs.context import JobContext, RunControl, job_log_path, publish_job
from yt_dlp_z.services.jobs.files import job_files
from yt_dlp_z.services.jobs.process import ProcessHooks, run_ytdlp
from yt_dlp_z.services.live_chat.overlay import CHAT_SUFFIX, OverlayResult, build_overlay
from yt_dlp_z.services.ytdlp.command import CHAT_MARKER, build_command
from yt_dlp_z.services.ytdlp.output import ChatUpdate, Update

logger = logging.getLogger(__name__)

# Only streams and premieres that have ended have a chat replay. A live capture is for later.
NO_REPLAY = {"not_live", "is_live", "is_upcoming"}
CHAT_FIELDS = "filepath,webpage_url,live_status"
# Worst first: what the job shows when a playlist's videos end differently.
STATUS_ORDER: tuple[ChatStatus, ...] = ("stopped", "failed", "overlay", "saved", "none")


@dataclass(frozen=True)
class ChatRun:
    context: JobContext
    session: AsyncSession
    job: Job
    videos: list[ChatUpdate]
    # --cookies and --proxy, as the video used.
    access_args: list[str]
    control: RunControl


def chat_settings(job: Job) -> LiveChatSettings | None:
    settings = LiveChatSettings.model_validate(job.live_chat) if job.live_chat else None
    return settings if settings and settings.mode != "off" else None


def chat_print_args(job: Job) -> list[str]:
    """Reports each saved video, so the chat step knows its link and file name. Recordings
    don't save chat yet; their VOD does."""
    if job.kind == JobKind.LIVE or chat_settings(job) is None:
        return []
    return ["--print", f"after_move:{CHAT_MARKER}%(.{{{CHAT_FIELDS}}})j"]


def chat_path_for(video: Path) -> Path:
    return video.with_name(video.stem + CHAT_SUFFIX)


def chat_files(job: Job) -> list[Path]:
    return [path for path in job_files(job) if path.name.endswith(CHAT_SUFFIX)]


def _chat_command(run: ChatRun, video: Path, url: str) -> list[str]:
    # A literal name in a yt-dlp template: only % means anything there.
    name = video.stem.replace("%", "%%")
    args = [
        "--skip-download",
        # A chat doesn't need a format; don't fail on one that's gone since the download.
        "--ignore-no-formats-error",
        "--no-playlist",
        "--write-subs",
        "--sub-langs",
        "live_chat",
        "--output",
        f"{name}.%(ext)s",
        *run.access_args,
    ]
    return build_command(run.context.settings.ytdlp_command, args, url, video.parent)


def _log(run: ChatRun, line: str) -> None:
    with job_log_path(run.context.settings, run.job.id).open("a", encoding="utf-8") as log:
        log.write(f"[yt-dlp-z] {line}\n")


def describe_overlay(path: Path, result: OverlayResult) -> str:
    return f"Chat overlay {path.name}: {result.shown} of {result.comments} comments shown."


async def _build(run: ChatRun, chat_path: Path, style: OverlayStyle) -> ChatStatus:
    try:
        result = await asyncio.to_thread(build_overlay, chat_path, style)
    except Exception:
        # Whatever a strange chat file does, the video and the JSON are saved.
        logger.exception("Couldn't build the chat overlay of job %s", run.job.id)
        _log(run, f"Couldn't build the chat overlay from {chat_path.name}.")
        return "failed"
    _log(run, describe_overlay(chat_path, result))
    return "overlay"


async def _ignore_update(_update: Update) -> None:
    return None


async def _fetch(run: ChatRun, update: ChatUpdate, settings: LiveChatSettings) -> ChatStatus | None:
    if update.live_status in NO_REPLAY:
        _log(run, f"No chat replay to fetch: this video is {update.live_status}.")
        return None
    video = Path(update.filepath)
    _log(run, f"Fetching the live chat of {video.name}.")
    log_path = job_log_path(run.context.settings, run.job.id)
    hooks = ProcessHooks(_ignore_update, run.control.on_start)
    result = await run_ytdlp(_chat_command(run, video, update.url), log_path, hooks)
    if run.control.is_cancelled():
        return "stopped"
    if result.returncode != 0:
        _log(run, "Couldn't fetch the live chat. The video itself is saved.")
        return "failed"
    chat_path = chat_path_for(video)
    if not chat_path.is_file():
        _log(run, "This video has no chat replay.")
        return "none"
    return await _build(run, chat_path, settings) if settings.mode == "overlay" else "saved"


async def _save_status(run: ChatRun, status: ChatStatus | None) -> None:
    await repository.save(run.session, run.job, chat_status=status)
    publish_job(run.context.hub, run.job)


async def run_chat_step(run: ChatRun) -> None:
    settings = chat_settings(run.job)
    if settings is None or not run.videos:
        return
    await _save_status(run, "fetching")
    found: set[ChatStatus] = set()
    for video in run.videos:
        status = await _fetch(run, video, settings)
        if status:
            found.add(status)
        if status == "stopped":
            break
    await _save_status(run, next((name for name in STATUS_ORDER if name in found), None))
