"""Finds the newest yt-dlp for a channel, once a day, and installs it when asked to."""

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from yt_dlp_z.schemas.ytdlp import YtdlpChannel, YtdlpPreferences
from yt_dlp_z.services.ytdlp.communicate import communicate
from yt_dlp_z.services.ytdlp.pip import last_line
from yt_dlp_z.services.ytdlp.updater import UpdateError, YtdlpUpdater

logger = logging.getLogger(__name__)

CHECK_TIMEOUT_SECONDS = 60
# The first check waits a little, so starting the app stays quick.
FIRST_CHECK_SECONDS = 60
CHECK_INTERVAL_SECONDS = 24 * 3600


def check_command(updater: YtdlpUpdater, channel: YtdlpChannel) -> list[str]:
    """pip's dry run resolves the version an update would install, without writing anything."""
    pre = ["--pre"] if channel == "nightly" else []
    target = str(updater.update_dir.with_name(f"{updater.update_dir.name}.check"))
    options = ["--dry-run", "--quiet", "--no-input", "--disable-pip-version-check"]
    report = ["--ignore-installed", "--report", "-", "--target", target]
    return [*updater.pip_command, "install", *options, *report, *pre, "yt-dlp"]


def _version_in_report(report: dict[str, Any]) -> str | None:
    for item in report.get("install") or []:
        meta = item.get("metadata") or {}
        if str(meta.get("name", "")).lower() == "yt-dlp":
            return str(meta.get("version"))
    return None


async def find_latest_version(updater: YtdlpUpdater, channel: YtdlpChannel) -> str:
    process = await asyncio.create_subprocess_exec(
        *check_command(updater, channel),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        async with asyncio.timeout(CHECK_TIMEOUT_SECONDS):
            output, _ = await communicate(process)
    except TimeoutError as error:
        raise UpdateError("Checking for updates timed out.") from error
    if process.returncode != 0:
        raise UpdateError(f"Couldn't check for updates: {last_line(output)}")
    try:
        version = _version_in_report(json.loads(output))
    except (json.JSONDecodeError, AttributeError) as error:
        raise UpdateError("pip's answer was in an unexpected format.") from error
    if version is None:
        raise UpdateError("pip didn't find yt-dlp.")
    return version


# Reads the stored channel and auto-update choice.
Preferences = Callable[[], Awaitable[YtdlpPreferences]]


class UpdateChecker:
    """Remembers the newest version found; with auto-update on, installs it."""

    def __init__(
        self,
        updater: YtdlpUpdater,
        preferences: Preferences,
        *,
        first_check_seconds: float = FIRST_CHECK_SECONDS,
    ) -> None:
        self._updater = updater
        self._preferences = preferences
        self._first_check_seconds = first_check_seconds
        self._loop: asyncio.Task[None] | None = None
        self.latest_version: str | None = None
        self.checked_at: datetime | None = None

    async def check(self, channel: YtdlpChannel) -> str:
        self.latest_version = await find_latest_version(self._updater, channel)
        self.checked_at = datetime.now(UTC)
        return self.latest_version

    async def check_and_update(self) -> None:
        preferences = await self._preferences()
        latest = await self.check(preferences.channel)
        newer = latest != self._updater.active_version
        if preferences.auto_update and newer and not self._updater.running:
            logger.info("Updating yt-dlp to %s automatically", latest)
            self._updater.start(preferences.channel)

    def start(self) -> None:
        self._loop = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._loop is None:
            return
        self._loop.cancel()
        await asyncio.gather(self._loop, return_exceptions=True)

    async def _run(self) -> None:
        await asyncio.sleep(self._first_check_seconds)
        while True:
            try:
                await self.check_and_update()
            except UpdateError as error:
                logger.warning("yt-dlp update check failed: %s", error)
            except Exception:
                logger.exception("The yt-dlp update check crashed; retrying tomorrow")
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)
