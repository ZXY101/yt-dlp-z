"""Saves a recording's live chat while it's being recorded.

A chat-only yt-dlp beside the recording, which it must never slow down or fail: it has its own
process and files, and everything that goes wrong here is only logged. It restarts if it stops
while the recording goes on. yt-dlp writes the chat out after each poll, so stopping it loses
at most the last few seconds. When the recording ends, split.py gives each saved part its chat.
"""

import asyncio
import contextlib
import logging
import time
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.job import Job
from yt_dlp_z.schemas.live_chat import ChatStatus, LiveChatSettings
from yt_dlp_z.services.cookies.store import working_copy
from yt_dlp_z.services.jobs import repository
from yt_dlp_z.services.jobs.context import JobContext, job_log_path, publish_job
from yt_dlp_z.services.jobs.process import ProcessHooks, run_ytdlp
from yt_dlp_z.services.live_chat.job_step import chat_settings
from yt_dlp_z.services.live_chat.overlay import CHAT_SUFFIX, build_overlay
from yt_dlp_z.services.live_chat.split import (
    SavedPart,
    capture_dir,
    capture_files,
    discard_capture,
    split_capture,
)
from yt_dlp_z.services.ytdlp.command import build_command
from yt_dlp_z.services.ytdlp.output import FileUpdate, InfoUpdate, ProgressUpdate, Update

logger = logging.getLogger(__name__)

# Like the recording's own wait for a stream: not every stream has a chat from the first moment.
RETRY_SECONDS = (30, 60, 120, 300)


async def _ignore_update(_update: Update) -> None:
    return None


class NoCapture:
    """A recording that doesn't save its chat."""

    def start(self, proxy_args: list[str]) -> None:
        pass

    def begin_part(self, part: int) -> None:
        pass

    def on_update(self, part: int, update: Update) -> None:
        pass

    def renamed(self, old: str, new: str) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def finish(self, session: AsyncSession) -> None:
        pass


class ChatCapture(NoCapture):
    def __init__(self, context: JobContext, job: Job, settings: LiveChatSettings) -> None:
        self._context = context
        self._job = job
        self._settings = settings
        self._folder = capture_dir(context.settings, job.id)
        self._task: asyncio.Task[None] | None = None
        self._proxy_args: list[str] = []
        self._located = False

    def start(self, proxy_args: list[str]) -> None:
        self._proxy_args = proxy_args
        if self._job.chat_capture is None:
            # SQLite can reuse a deleted job's id; a new job must not inherit its chat.
            discard_capture(self._context.settings, self._job.id)
            self._job.chat_capture = {"parts": []}
        self._job.chat_status = "capturing"
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        try:
            if self._job.cookie_id is None:
                await self._keep_capturing(self._proxy_args)
                return
            # Its own copy: yt-dlp writes cookies back when it exits, and so does the recording.
            config_dir = self._context.settings.config_dir
            copy = working_copy(config_dir, self._job.cookie_id, f"job-{self._job.id}-chat")
            with copy as path:
                await self._keep_capturing(["--cookies", str(path), *self._proxy_args])
        except Exception:
            logger.exception("The live chat capture of job %s stopped", self._job.id)

    def _command(self, run: int, access_args: list[str]) -> list[str]:
        args = [
            "--skip-download",
            # An upcoming stream has no formats yet, but may already have its waiting room chat.
            "--ignore-no-formats-error",
            "--no-playlist",
            "--write-subs",
            "--sub-langs",
            "live_chat",
            "--output",
            f"chat-{run}.%(ext)s",
            *access_args,
        ]
        ytdlp = self._context.settings.ytdlp_command
        return build_command(ytdlp, args, self._job.url, self._folder)

    async def _keep_capturing(self, access_args: list[str]) -> None:
        self._folder.mkdir(parents=True, exist_ok=True)
        log_path = job_log_path(self._context.settings, self._job.id)
        hooks = ProcessHooks(_ignore_update, lambda _process: None)
        waits = 0
        while True:
            run = len(capture_files(self._folder)) + 1
            result = await run_ytdlp(self._command(run, access_args), log_path, hooks)
            ended = (self._folder / f"chat-{run}{CHAT_SUFFIX}").is_file()
            if result.returncode == 0 and ended:
                return  # The stream ended; a finished file means it ran to the end.
            await asyncio.sleep(RETRY_SECONDS[min(waits, len(RETRY_SECONDS) - 1)])
            waits += 1

    def _set_part(self, part: int, **changes: object) -> None:
        parts: list[dict[str, object]] = [
            {**entry, **changes} if entry["part"] == part else entry
            for entry in (self._job.chat_capture or {})["parts"]
        ]
        # A new object, so SQLAlchemy sees the change to the JSON column.
        self._job.chat_capture = {"parts": parts}

    def begin_part(self, part: int) -> None:
        self._located = False
        entry = {"part": part, "started": time.time(), "file": None}
        parts = [*(self._job.chat_capture or {})["parts"], entry]
        self._job.chat_capture = {"parts": parts}

    def on_update(self, part: int, update: Update) -> None:
        """A part recorded from the stream's start begins at the stream's start. One recorded
        from now begins when its first data arrives: what viewers were seeing then, so a
        comment lands on the moment the viewer was watching."""
        if isinstance(update, InfoUpdate) and update.release_timestamp:
            if part == 1 and self._job.record_from_start:
                self._set_part(part, started=update.release_timestamp)
                self._located = True
        elif isinstance(update, ProgressUpdate) and not self._located:
            self._set_part(part, started=time.time())
            self._located = True
        elif isinstance(update, FileUpdate):
            self._set_part(part, file=update.filepath)

    def renamed(self, old: str, new: str) -> None:
        parts = (self._job.chat_capture or {})["parts"]
        for entry in parts:
            if entry["file"] == old:
                self._set_part(entry["part"], file=new)

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    def _saved_parts(self) -> list[SavedPart]:
        parts = (self._job.chat_capture or {})["parts"]
        return [
            SavedPart(Path(entry["file"]), float(entry["started"]))
            for entry in parts
            if entry["file"] and Path(entry["file"]).is_file()
        ]

    def _write_files(self) -> ChatStatus:
        chats = split_capture(self._folder, self._saved_parts())
        if not chats:
            return "none"
        if self._settings.mode == "overlay":
            for chat in chats:
                build_overlay(chat, self._settings)
            return "overlay"
        return "saved"

    def _log(self, line: str) -> None:
        log_path = job_log_path(self._context.settings, self._job.id)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"[yt-dlp-z] {line}\n")

    async def finish(self, session: AsyncSession) -> None:
        """Gives each saved part its chat. The capture folder stays if this fails, until the
        download is removed, so what was captured isn't lost."""
        status: ChatStatus
        try:
            status = await asyncio.to_thread(self._write_files)
        except Exception:
            logger.exception("Couldn't save the live chat of job %s", self._job.id)
            self._log("Couldn't save the live chat. The recording itself is saved.")
            status = "failed"
        if status != "failed":
            discard_capture(self._context.settings, self._job.id)
        self._log(f"Live chat: {status}.")
        await repository.save(session, self._job, chat_status=status)
        publish_job(self._context.hub, self._job)


def capture_for(context: JobContext, job: Job) -> NoCapture:
    settings = chat_settings(job)
    return ChatCapture(context, job, settings) if settings else NoCapture()
