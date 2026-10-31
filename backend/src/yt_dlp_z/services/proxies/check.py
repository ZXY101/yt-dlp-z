"""The proxies "Test" button (see check_script.py)."""

import asyncio
import json

from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.job import utcnow
from yt_dlp_z.db.models.proxy import Proxy
from yt_dlp_z.services.proxies.store import hide_password
from yt_dlp_z.services.ytdlp.communicate import communicate

CHECK_TIMEOUT_SECONDS = 60


class CheckResult(BaseModel):
    ok: bool
    exit_ip: str | None
    error: str | None


async def _run_check(check_command: list[str], proxy_url: str) -> CheckResult:
    process = await asyncio.create_subprocess_exec(
        *check_command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        async with asyncio.timeout(CHECK_TIMEOUT_SECONDS):
            stdout, _ = await communicate(process, proxy_url.encode())
    except TimeoutError:
        return CheckResult(ok=False, exit_ip=None, error="The proxy took too long to answer.")
    try:
        return CheckResult.model_validate(json.loads(stdout))
    except (json.JSONDecodeError, ValidationError):
        error = f"The proxy check exited with code {process.returncode}."
        return CheckResult(ok=False, exit_ip=None, error=error)


async def check_proxy(session: AsyncSession, check_command: list[str], proxy: Proxy) -> Proxy:
    result = await _run_check(check_command, proxy.url)
    proxy.checked_at = utcnow()
    proxy.check_ok = result.ok
    proxy.exit_ip = result.exit_ip
    proxy.check_error = hide_password(result.error, proxy.url)
    if result.ok:
        # It works again: no need to wait out a cooldown.
        proxy.cooldown_until = None
    await session.commit()
    await session.refresh(proxy)
    return proxy
