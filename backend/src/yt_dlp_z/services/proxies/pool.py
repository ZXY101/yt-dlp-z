"""Picks the proxy a job runs through. The pick is kept for the whole job."""

import secrets
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.job import Job, utcnow
from yt_dlp_z.db.models.proxy import Proxy
from yt_dlp_z.services.proxies.store import get_proxy_settings, is_available, list_proxies


class NoProxyError(Exception):
    pass


class ProxyPool:
    def __init__(self) -> None:
        # Rotation position, shared by every preset that rotates. Starts over on restart.
        self._turn = 0

    async def pick(self, session: AsyncSession, job: Job, tried: set[int]) -> Proxy | None:
        """The proxy for this job, or None to connect directly. `tried`: proxies that
        already failed this job. Raises NoProxyError rather than going direct, so a
        pool used to hide the server's IP never leaks it."""
        if job.proxy_mode == "off":
            return None
        if job.cookie_id is not None and not (await get_proxy_settings(session)).send_cookies:
            return None
        now = utcnow()
        proxies = await list_proxies(session)
        free = [p for p in proxies if is_available(p, now) and p.id not in tried]
        if not free:
            raise NoProxyError(_no_proxy_message(proxies, tried))
        return self.choose(free, job)

    def choose(self, free: Sequence[Proxy], job: Job) -> Proxy:
        if job.proxy_mode == "random":
            return secrets.choice(free)
        if job.proxy_mode == "sticky" and job.subscription_id is not None:
            # Same channel, same proxy, as long as the pool doesn't change.
            return free[job.subscription_id % len(free)]
        # Rotation (and sticky for one-off downloads, which have no channel to stick to).
        proxy = free[self._turn % len(free)]
        self._turn += 1
        return proxy


def _no_proxy_message(proxies: Sequence[Proxy], tried: set[int]) -> str:
    if tried:
        return "Every proxy this download tried was blocked or didn't connect. Retry it later."
    if not any(proxy.enabled for proxy in proxies):
        return "This preset uses the proxy pool, but no proxy is turned on (Settings → Proxies)."
    return "Every proxy is cooling down after being blocked or not connecting. Retry later."
