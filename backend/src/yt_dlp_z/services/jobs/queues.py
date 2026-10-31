"""Downloads and recordings run in separate queues, so a long recording never holds up
downloads (and a full download queue never delays a stream that is about to start)."""

from yt_dlp_z.db.models.job import Job, JobKind
from yt_dlp_z.services.jobs import repository
from yt_dlp_z.services.jobs.context import JobContext
from yt_dlp_z.services.jobs.manager import JobManager


class JobQueues:
    def __init__(self, context: JobContext, download_limit: int, recording_limit: int) -> None:
        self._context = context
        self.downloads = JobManager(context, download_limit)
        self.recordings = JobManager(context, recording_limit)

    def _manager(self, kind: JobKind) -> JobManager:
        return self.recordings if kind == JobKind.LIVE else self.downloads

    async def start(self) -> None:
        async with self._context.session_factory() as session:
            for job_id, kind in await repository.recover_after_restart(session):
                self._manager(kind).submit(job_id)
        self.downloads.start()
        self.recordings.start()

    async def stop(self) -> None:
        await self.downloads.stop()
        await self.recordings.stop()

    async def stop_all(self) -> None:
        await self.downloads.stop_all()
        await self.recordings.stop_all()

    def submit(self, job: Job) -> None:
        self._manager(job.kind).submit(job.id)

    async def cancel(self, job: Job) -> None:
        # A stopped recording keeps what it recorded so far.
        await self._manager(job.kind).cancel(job.id, graceful=job.kind == JobKind.LIVE)
