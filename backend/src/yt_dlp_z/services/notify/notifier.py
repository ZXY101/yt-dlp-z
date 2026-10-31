"""Turns job events into ntfy notifications."""

import asyncio
import logging
from collections.abc import Awaitable, Callable

from yt_dlp_z.schemas.notifications import NotifyEvent
from yt_dlp_z.services.events import Event
from yt_dlp_z.services.notify import messages
from yt_dlp_z.services.notify.messages import FAILURE_STREAK, Job
from yt_dlp_z.services.notify.ntfy import Message, NotifyError, send_ntfy
from yt_dlp_z.services.notify.store import NtfyConfig

logger = logging.getLogger(__name__)

Send = Callable[[NtfyConfig, Message], Awaitable[None]]


class Notifier:
    """Listens to the event hub. Sending happens in the background; failures are logged."""

    def __init__(self, config: NtfyConfig, send: Send = send_ntfy) -> None:
        self.config = config
        self._send = send
        self._tasks: set[asyncio.Task[None]] = set()
        # Recordings already announced: running jobs publish every progress update.
        self._recording: set[int] = set()
        self._failures = 0

    def on_event(self, event: Event) -> None:
        if event.get("type") == "job":
            self._on_job(event["job"])

    def _on_job(self, job: Job) -> None:
        status = job["status"]
        if status == "running" and job["kind"] == "live" and job["id"] not in self._recording:
            self._recording.add(job["id"])
            self._notify("recording_started", messages.recording_started(job))
        elif status == "completed":
            self._recording.discard(job["id"])
            self._failures = 0
            self._notify("download_finished", messages.finished(job))
        elif status == "failed":
            self._recording.discard(job["id"])
            self._on_failure(job)
        elif status == "cancelled":
            self._recording.discard(job["id"])

    def _on_failure(self, job: Job) -> None:
        self._notify("download_failed", messages.failed(job))
        self._failures += 1
        cookies = messages.needs_cookies(job)
        if cookies is not None:
            self._notify("problems", cookies)
        elif self._failures == FAILURE_STREAK:
            # Once per streak; a finished download starts counting again.
            self._notify("problems", messages.failure_streak())

    def _notify(self, event: NotifyEvent, message: Message) -> None:
        config = self.config
        if not config.enabled or event not in config.events:
            return
        task = asyncio.get_running_loop().create_task(self._deliver(config, message))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _deliver(self, config: NtfyConfig, message: Message) -> None:
        try:
            await self._send(config, message)
        except NotifyError as error:
            logger.warning("Notification %r not sent: %s", message.title, error)

    async def send_test(self, config: NtfyConfig) -> None:
        """Raises NotifyError when it can't be sent."""
        await self._send(config, messages.test_message())

    async def drain(self) -> None:
        """Waits for notifications on their way (tests, shutdown)."""
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        await self.drain()
