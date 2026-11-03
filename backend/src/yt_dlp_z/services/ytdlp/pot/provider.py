"""Hands yt-dlp PO tokens from a bgutil server, when the user has set one up.

YouTube asks some clients for a PO token before it serves their formats; without one
yt-dlp skips those formats or gets HTTP 403 errors. A bgutil server makes the tokens and
the bgutil yt-dlp plugin fetches them (see plugin.py).
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path

from yt_dlp_z.services.ytdlp.global_args import set_global_args
from yt_dlp_z.services.ytdlp.pot.plugin import (
    install_plugin,
    plugin_args,
    plugin_version,
    remove_plugin,
)
from yt_dlp_z.services.ytdlp.pot.server import PotError, server_version

logger = logging.getLogger(__name__)

# How often the server's version is checked, so a server update brings the matching plugin.
SYNC_INTERVAL_SECONDS = 6 * 60 * 60

# Reads the saved provider URL ("" or None means off).
LoadUrl = Callable[[], Awaitable[str | None]]


class PotProvider:
    def __init__(self, pip_command: list[str], plugins_dir: Path, load_url: LoadUrl) -> None:
        self._pip_command = pip_command
        self._plugins_dir = plugins_dir
        self._load_url = load_url
        self._lock = asyncio.Lock()
        self._loop: asyncio.Task[None] | None = None
        self.url: str | None = None
        # From the last check of the server.
        self.server_version: str | None = None
        self.error: str | None = None
        self.checked_at: datetime | None = None

    @property
    def plugin_version(self) -> str | None:
        return plugin_version(self._plugins_dir)

    async def configure(self, url: str | None) -> None:
        """Turns PO tokens on for the server at url (None turns them off). Raises PotError
        if the server can't be reached or its plugin can't be installed; nothing changes."""
        async with self._lock:
            if url is None:
                self._turn_off()
                return
            await self._connect(url)

    async def sync(self) -> None:
        """Checks the saved server again and installs its plugin version if it changed.
        An unreachable server is only remembered: yt-dlp keeps asking it for tokens."""
        url = await self._load_url() or None
        async with self._lock:
            if url is None:
                self._turn_off()
                return
            self._use(url)
            try:
                await self._connect(url)
            except PotError as error:
                self.error = str(error)
                self.checked_at = datetime.now(UTC)
                logger.warning("PO token provider check failed: %s", error)

    async def start(self) -> None:
        # Downloads started before the first check already get the plugin.
        url = await self._load_url() or None
        if url is not None:
            self._use(url)
        self._loop = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._loop is None:
            return
        self._loop.cancel()
        await asyncio.gather(self._loop, return_exceptions=True)

    async def _connect(self, url: str) -> None:
        version = await server_version(url)
        if self.plugin_version != version:
            logger.info("Installing the PO token plugin %s", version)
            await install_plugin(self._pip_command, self._plugins_dir, version)
        self._use(url)
        self.server_version = version
        self.error = None
        self.checked_at = datetime.now(UTC)

    def _use(self, url: str) -> None:
        self.url = url
        has_plugin = self.plugin_version is not None
        set_global_args(plugin_args(self._plugins_dir, url) if has_plugin else [])

    def _turn_off(self) -> None:
        set_global_args([])
        remove_plugin(self._plugins_dir)
        self.url = None
        self.server_version = None
        self.error = None
        self.checked_at = None

    async def _run(self) -> None:
        while True:
            try:
                await self.sync()
            except Exception:
                logger.exception("The PO token provider check crashed; retrying later")
            await asyncio.sleep(SYNC_INTERVAL_SECONDS)
