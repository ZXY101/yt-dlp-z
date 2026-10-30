"""Updates yt-dlp without rebuilding the image or reinstalling the app.

Updates are pip-installed into <config>/ytdlp. That folder comes first on PYTHONPATH for
every yt-dlp subprocess (see ytdlp_python_path), so an update survives container rebuilds,
and deleting the folder goes back to the yt-dlp bundled with the app.
"""

import asyncio
import os
import shutil
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path

from yt_dlp_z.schemas.ytdlp import UpdateState, UpdateStatus, YtdlpChannel
from yt_dlp_z.services.ytdlp.communicate import communicate

PACKAGE = "yt-dlp[default]"
TIMEOUT_SECONDS = 600


class UpdateError(Exception):
    pass


class UpdateRunningError(Exception):
    pass


@contextmanager
def ytdlp_python_path(update_dir: Path) -> Iterator[None]:
    """Puts the update folder first on PYTHONPATH while the app runs. yt-dlp subprocesses
    inherit the app's environment; a missing folder is ignored by Python."""
    previous = os.environ.get("PYTHONPATH")
    os.environ["PYTHONPATH"] = os.pathsep.join(filter(None, [str(update_dir), previous]))
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = previous


def bundled_version() -> str:
    return metadata.version("yt-dlp")


def updated_version(update_dir: Path) -> str | None:
    """The yt-dlp version installed in the update folder, if any."""
    for dist_info in update_dir.glob("yt_dlp-*.dist-info"):
        return metadata.PathDistribution(dist_info).version
    return None


def install_command(pip_command: list[str], target: Path, channel: YtdlpChannel) -> list[str]:
    # Nightly builds are published to PyPI as pre-releases (yt-dlp's own install docs).
    pre = ["--pre"] if channel == "nightly" else []
    options = ["--upgrade", "--no-input", "--disable-pip-version-check", "--target", str(target)]
    return [*pip_command, "install", *options, *pre, PACKAGE]


def _last_line(output: bytes) -> str:
    lines = output.decode(errors="replace").strip().splitlines()
    return lines[-1] if lines else "no output"


class YtdlpUpdater:
    """Runs one update at a time in the background and remembers how the last one went."""

    def __init__(
        self, pip_command: list[str], update_dir: Path, on_change: Callable[[], None]
    ) -> None:
        self._pip_command = pip_command
        self._update_dir = update_dir
        self._on_change = on_change
        self._task: asyncio.Task[None] | None = None
        self.status = UpdateStatus(state="idle")

    @property
    def active_version(self) -> str:
        return updated_version(self._update_dir) or bundled_version()

    @property
    def using_update(self) -> bool:
        return updated_version(self._update_dir) is not None

    def start(self, channel: YtdlpChannel) -> None:
        if self.status.state == "running":
            raise UpdateRunningError
        self.status = UpdateStatus(state="running")
        self._task = asyncio.create_task(self._run(channel))

    def reset(self) -> None:
        """Goes back to the bundled yt-dlp."""
        if self.status.state == "running":
            raise UpdateRunningError
        shutil.rmtree(self._update_dir, ignore_errors=True)
        self.status = UpdateStatus(state="idle")
        self._on_change()

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)

    async def _run(self, channel: YtdlpChannel) -> None:
        previous = self.active_version
        try:
            await self._install(channel)
        except UpdateError as error:
            self.status = self._finished("failed", str(error))
            return
        current = self.active_version
        if current == previous:
            self.status = self._finished("succeeded", f"yt-dlp {current} is the newest version.")
        else:
            self.status = self._finished("succeeded", f"Updated yt-dlp to {current}.")
        self._on_change()

    async def _install(self, channel: YtdlpChannel) -> None:
        # Installed next to the live folder, then swapped in, so a failed or half-done
        # install never breaks the yt-dlp in use.
        staging = self._update_dir.with_name(f"{self._update_dir.name}.new")
        shutil.rmtree(staging, ignore_errors=True)
        staging.parent.mkdir(parents=True, exist_ok=True)
        try:
            await self._pip_install(install_command(self._pip_command, staging, channel))
            version = updated_version(staging)
            if version is None:
                raise UpdateError("pip finished but yt-dlp wasn't installed.")
            if version == bundled_version():
                # Nothing newer than the app's own copy (or back from nightly to stable).
                shutil.rmtree(self._update_dir, ignore_errors=True)
            else:
                self._swap_in(staging)
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    async def _pip_install(self, command: list[str]) -> None:
        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )
        try:
            async with asyncio.timeout(TIMEOUT_SECONDS):
                output, _ = await communicate(process)
        except TimeoutError as error:
            raise UpdateError("The update timed out.") from error
        if process.returncode != 0:
            raise UpdateError(f"The update failed: {_last_line(output)}")

    def _swap_in(self, staging: Path) -> None:
        old = self._update_dir.with_name(f"{self._update_dir.name}.old")
        shutil.rmtree(old, ignore_errors=True)
        if self._update_dir.exists():
            self._update_dir.rename(old)
        staging.rename(self._update_dir)
        shutil.rmtree(old, ignore_errors=True)

    @staticmethod
    def _finished(state: UpdateState, message: str) -> UpdateStatus:
        return UpdateStatus(state=state, message=message, finished_at=datetime.now(UTC))
