"""The proxy side of running a job (see services/proxies)."""

from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.job import Job, JobStatus
from yt_dlp_z.services.live.recorder import Outcome
from yt_dlp_z.services.proxies.blocks import is_proxy_block
from yt_dlp_z.services.proxies.pool import ProxyPool
from yt_dlp_z.services.proxies.store import get_proxy, hide_password, start_cooldown


async def use_proxy(pool: ProxyPool, session: AsyncSession, job: Job, tried: set[int]) -> list[str]:
    """Picks the job's proxy (saved with the job's next save) and returns its --proxy.
    Raises NoProxyError when the job should use one but none is free."""
    proxy = await pool.pick(session, job, tried)
    job.proxy_id = proxy.id if proxy else None
    return ["--proxy", proxy.url] if proxy else []


async def cool_down_if_blocked(session: AsyncSession, job: Job, outcome: Outcome) -> bool:
    status, error = outcome
    if job.proxy_id is None or status != JobStatus.FAILED or not is_proxy_block(error):
        return False
    await start_cooldown(session, job.proxy_id)
    return True


async def hide_proxy_password(session: AsyncSession, job: Job, outcome: Outcome) -> Outcome:
    proxy = await get_proxy(session, job.proxy_id) if job.proxy_id is not None else None
    if proxy is None:
        return outcome
    status, error = outcome
    return status, hide_password(error, proxy.url)
