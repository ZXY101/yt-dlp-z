"""Runs alignment jobs in the background and makes sure their audio never stays around.

Jobs live in memory only. A job's files sit in <root>/<id>/ while it runs and are deleted
as soon as it finishes or fails; the result is dropped on DELETE or after an hour without
a status check. The whole root is wiped at startup and shutdown.
"""

import asyncio
import contextlib
import logging
import secrets
import shutil
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

from yt_dlp_z.services.align.fetch import (
    FetchError,
    FetchHooks,
    FetchRequest,
    Tools,
    fetch_audio,
)
from yt_dlp_z.services.align.job import (
    AlignBusyError,
    AlignJob,
    AlignState,
    StreamProgress,
    StreamStage,
)
from yt_dlp_z.services.align.matching import match_pair
from yt_dlp_z.services.cookies.store import cookie_path, working_copy

logger = logging.getLogger(__name__)

IDLE_SECONDS = 3600
# A running job nobody checks on is abandoned (clients poll every few seconds): stop it then,
# rather than keep downloading for nobody.
RUNNING_IDLE_SECONDS = 60
SWEEP_SECONDS = 15
# Finished results kept for clients to read; the oldest go first.
MAX_KEPT = 20
# Below this share of agreeing windows an offset is reported as not found.
MIN_CONFIDENCE = 0.5
PRIVATE_DIR_MODE = 0o700


@dataclass(frozen=True)
class AlignConfig:
    root: Path
    config_dir: Path
    tools: Tools
    clock: Callable[[], float] = time.monotonic


class AlignManager:
    def __init__(self, config: AlignConfig) -> None:
        self._config = config
        self._jobs: dict[str, AlignJob] = {}
        self._sweeper: asyncio.Task[None] | None = None

    def start(self) -> None:
        self._wipe()
        self._sweeper = asyncio.create_task(self._sweep_forever())

    async def stop(self) -> None:
        if self._sweeper is not None:
            self._sweeper.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._sweeper
        for job_id in list(self._jobs):
            await self.delete(job_id)
        self._wipe()

    def create(self, urls: list[str], cookie_id: int | None) -> AlignJob:
        if any(job.running for job in self._jobs.values()):
            raise AlignBusyError("Another alignment is running. Try again when it's done.")
        self._drop_oldest_finished()
        job_id = secrets.token_urlsafe(16)
        job = AlignJob(id=job_id, urls=urls, last_seen=self._config.clock())
        job.streams = [StreamProgress(url) for url in urls]
        job.task = asyncio.create_task(self._run(job, cookie_id))
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> AlignJob | None:
        job = self._jobs.get(job_id)
        if job is not None:
            job.last_seen = self._config.clock()
        return job

    async def delete(self, job_id: str) -> bool:
        job = self._jobs.pop(job_id, None)
        if job is None:
            return False
        if job.task is not None and not job.task.done():
            job.task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await job.task
        shutil.rmtree(self._config.root / job_id, ignore_errors=True)
        return True

    async def sweep(self) -> None:
        """Drops jobs nobody has asked about (a closed browser): running ones after
        RUNNING_IDLE_SECONDS, finished results after IDLE_SECONDS."""
        now = self._config.clock()
        for job in list(self._jobs.values()):
            limit = RUNNING_IDLE_SECONDS if job.running else IDLE_SECONDS
            if job.last_seen < now - limit:
                await self.delete(job.id)

    async def _sweep_forever(self) -> None:
        while True:
            await asyncio.sleep(SWEEP_SECONDS)
            await self.sweep()

    def _drop_oldest_finished(self) -> None:
        finished = [job for job in self._jobs.values() if not job.running]
        finished.sort(key=lambda job: job.last_seen)
        for job in finished[: max(0, len(finished) - MAX_KEPT + 1)]:
            self._jobs.pop(job.id, None)

    def _wipe(self) -> None:
        shutil.rmtree(self._config.root, ignore_errors=True)

    async def _run(self, job: AlignJob, cookie_id: int | None) -> None:
        workdir = self._config.root / job.id
        workdir.mkdir(parents=True, mode=PRIVATE_DIR_MODE)
        try:
            files = await self._fetch_all(job, workdir, cookie_id)
            job.state = AlignState.ANALYSING
            await asyncio.to_thread(self._match_all, job, files)
            job.state = AlignState.DONE
        except FetchError as error:
            job.state, job.error = AlignState.FAILED, str(error)
        except Exception:
            logger.exception("Alignment %s failed", job.id)
            job.state, job.error = AlignState.FAILED, "Alignment failed unexpectedly"
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    async def _fetch_all(self, job: AlignJob, workdir: Path, cookie_id: int | None) -> list[Path]:
        async def fetch(index: int, url: str) -> Path:
            stream = job.streams[index]

            async def on_progress(progress: float) -> None:
                stream.downloaded = progress

            def on_converting() -> None:
                stream.stage = StreamStage.CONVERTING

            with self._cookies(cookie_id, f"align-{job.id}-{index}") as cookies:
                request = FetchRequest(url, workdir, f"audio-{index}", cookies)
                hooks = FetchHooks(on_progress, on_converting)
                path = await fetch_audio(self._config.tools, request, hooks)
            stream.stage = StreamStage.READY
            return path

        tasks = [asyncio.create_task(fetch(i, url)) for i, url in enumerate(job.urls)]
        try:
            return list(await asyncio.gather(*tasks))
        except BaseException:
            # One link failed (or the job was stopped): the others' downloads are no use.
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

    @contextlib.contextmanager
    def _cookies(self, cookie_id: int | None, owner: str) -> Iterator[Path | None]:
        if cookie_id is None:
            yield None
            return
        if not cookie_path(self._config.config_dir, cookie_id).exists():
            raise FetchError("That cookies file doesn't exist")
        with working_copy(self._config.config_dir, cookie_id, owner) as path:
            yield path

    @staticmethod
    def _match_all(job: AlignJob, files: list[Path]) -> None:
        first, *others = files
        job.offsets[job.urls[0]] = 0.0
        job.confidence[job.urls[0]] = 1.0
        for url, path in zip(job.urls[1:], others, strict=True):
            match = match_pair(first, path)
            confidence = match.confidence if match else 0.0
            job.confidence[url] = round(confidence, 2)
            found = match if match and confidence >= MIN_CONFIDENCE else None
            job.offsets[url] = round(found.offset, 3) if found else None
