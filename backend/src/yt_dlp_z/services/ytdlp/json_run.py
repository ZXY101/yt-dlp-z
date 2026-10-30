"""Runs yt-dlp for metadata only (-J) and returns the parsed JSON."""

import asyncio
import json
from typing import Any

from yt_dlp_z.services.ytdlp.communicate import communicate
from yt_dlp_z.services.ytdlp.output import error_message

JSON_TIMEOUT_SECONDS = 120


class YtdlpJsonError(Exception):
    """yt-dlp failed or printed no JSON. The message is yt-dlp's last error line."""


def _last_error(output: str) -> str | None:
    errors = [error_message(line) for line in output.splitlines()]
    found = [error for error in errors if error]
    return found[-1] if found else None


async def run_ytdlp_json(ytdlp_command: list[str], args: list[str], url: str) -> dict[str, Any]:
    command = [*ytdlp_command, "--ignore-config", "--no-warnings", "-J", *args, "--", url]
    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        async with asyncio.timeout(JSON_TIMEOUT_SECONDS):
            stdout, stderr = await communicate(process)
    except TimeoutError:
        raise YtdlpJsonError("yt-dlp took too long to answer.") from None
    if process.returncode != 0:
        error = _last_error(stderr.decode(errors="replace"))
        raise YtdlpJsonError(error or f"yt-dlp exited with code {process.returncode}.")
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        raise YtdlpJsonError("yt-dlp printed something that isn't JSON.") from None
    if not isinstance(data, dict):
        raise YtdlpJsonError("yt-dlp printed something that isn't JSON.")
    return data
