import asyncio
import contextlib
import functools
import logging

from yt_dlp_z.db.models.job import JobStatus, utcnow
from yt_dlp_z.services.jobs import repository
from yt_dlp_z.services.jobs.job_run import JobContext, execute_job, publish_job
from yt_dlp_z.services.jobs.process import stop_process

logger = logging.getLogger(__name__)

FINISH_TIMEOUT_SECONDS = 15


class JobManager:
    """Queue of download jobs, running at most `limit` at a time. The limit can change
    while running: lowering it lets current downloads finish instead of stopping them."""

    def __init__(self, context: JobContext, limit: int) -> None:
        self._context = context
        self._queue: asyncio.Queue[int] = asyncio.Queue()
        self._limit = max(1, limit)
        self._slot_freed = asyncio.Event()
        self._dispatcher: asyncio.Task[None] | None = None
        self._running: set[asyncio.Task[None]] = set()
        self._processes: dict[int, asyncio.subprocess.Process] = {}
        self._cancelled: set[int] = set()
        self._finished: dict[int, asyncio.Event] = {}

    def start(self) -> None:
        self._dispatcher = asyncio.create_task(self._dispatch())

    async def stop(self) -> None:
        # Running jobs stay "running" in the DB; recover_after_restart marks them
        # interrupted on the next start.
        tasks = [*self._running, *([self._dispatcher] if self._dispatcher else [])]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        for process in list(self._processes.values()):
            await stop_process(process)

    @property
    def limit(self) -> int:
        return self._limit

    def set_limit(self, limit: int) -> None:
        self._limit = max(1, limit)
        self._slot_freed.set()

    def submit(self, job_id: int) -> None:
        self._queue.put_nowait(job_id)

    async def cancel(self, job_id: int, graceful: bool = False) -> None:
        """Stops a running job and waits until its final status is saved.
        Queued jobs only need their DB status changed. `graceful`: see stop_process."""
        self._cancelled.add(job_id)
        finished = self._finished.get(job_id)
        process = self._processes.get(job_id)
        if process is not None:
            await stop_process(process, graceful=graceful)
        if finished is not None:
            await asyncio.wait_for(finished.wait(), FINISH_TIMEOUT_SECONDS)

    async def stop_all(self) -> None:
        """Cancels every running job and empties the queue (used by the test reset)."""
        while not self._queue.empty():
            self._queue.get_nowait()
            self._queue.task_done()
        for job_id in list(self._processes):
            await self.cancel(job_id)

    async def _dispatch(self) -> None:
        """Starts queued jobs in order, waiting for a free slot before each one."""
        while True:
            job_id = await self._queue.get()
            while len(self._running) >= self._limit:
                self._slot_freed.clear()
                await self._slot_freed.wait()
            task = asyncio.create_task(self._run(job_id))
            self._running.add(task)
            task.add_done_callback(self._release_slot)

    def _release_slot(self, task: asyncio.Task[None]) -> None:
        self._running.discard(task)
        self._slot_freed.set()

    async def _run(self, job_id: int) -> None:
        finished = self._finished[job_id] = asyncio.Event()
        try:
            await execute_job(
                self._context,
                job_id,
                on_start=functools.partial(self._on_start, job_id),
                is_cancelled=functools.partial(self._is_cancelled, job_id),
            )
        except Exception:
            logger.exception("Job %s crashed", job_id)
            await self._mark_crashed(job_id)
        finally:
            self._processes.pop(job_id, None)
            self._cancelled.discard(job_id)
            self._finished.pop(job_id, None)
            finished.set()
            self._queue.task_done()

    def _is_cancelled(self, job_id: int) -> bool:
        return job_id in self._cancelled

    def _on_start(self, job_id: int, process: asyncio.subprocess.Process) -> None:
        self._processes[job_id] = process
        if job_id in self._cancelled:
            # Cancelled between being picked up and the process starting.
            asyncio.get_running_loop().create_task(stop_process(process))

    async def _mark_crashed(self, job_id: int) -> None:
        with contextlib.suppress(Exception):
            async with self._context.session_factory() as session:
                job = await repository.get_job(session, job_id)
                if job is not None and job.status in {JobStatus.QUEUED, JobStatus.RUNNING}:
                    error = "yt-dlp-z hit an internal error. See the server log."
                    await repository.save(
                        session, job, status=JobStatus.FAILED, error=error, finished_at=utcnow()
                    )
                    publish_job(self._context.hub, job)
