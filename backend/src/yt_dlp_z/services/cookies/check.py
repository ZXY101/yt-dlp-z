"""The cookies "Test" button: asks yt-dlp to read one signed-in page without downloading."""

import asyncio
from pathlib import Path

from yt_dlp_z.schemas.cookies import CookieCheckResult
from yt_dlp_z.services.ytdlp.output import error_message

CHECK_TIMEOUT_SECONDS = 60


def check_command(ytdlp_command: list[str], cookie_file: Path, url: str) -> list[str]:
    return [
        *ytdlp_command,
        "--ignore-config",
        "--simulate",
        "--playlist-items",
        "1",
        "--no-warnings",
        "--print",
        "%(title)s",
        "--cookies",
        str(cookie_file),
        "--",
        url,
    ]


def _last_error(output: str) -> str | None:
    errors = [error_message(line) for line in output.splitlines()]
    found = [error for error in errors if error]
    return found[-1] if found else None


async def check_cookies(ytdlp_command: list[str], cookie_file: Path, url: str) -> CookieCheckResult:
    process = await asyncio.create_subprocess_exec(
        *check_command(ytdlp_command, cookie_file, url),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        stdout, _ = await asyncio.wait_for(process.communicate(), CHECK_TIMEOUT_SECONDS)
    except TimeoutError:
        process.kill()
        await process.wait()
        return CookieCheckResult(ok=False, message="yt-dlp took too long to answer.")
    output = stdout.decode(errors="replace")
    if process.returncode == 0:
        title = output.strip().splitlines()[-1:] or ["(no title)"]
        return CookieCheckResult(ok=True, message=f"Opened “{title[0]}” with these cookies.")
    error = _last_error(output) or f"yt-dlp exited with code {process.returncode}."
    return CookieCheckResult(ok=False, message=error)
