from collections.abc import Sequence
from datetime import datetime, timedelta
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.job import utcnow
from yt_dlp_z.db.models.proxy import Proxy
from yt_dlp_z.schemas.proxies import ProxyCreate, ProxySettings, ProxyUpdate
from yt_dlp_z.services.settings_store import get_value, set_values

# How long a proxy YouTube blocked (or that couldn't connect) is skipped.
COOLDOWN = timedelta(minutes=30)
SEND_COOKIES = "proxy_send_cookies"


class DuplicateProxyError(ValueError):
    pass


def masked_url(url: str) -> str:
    parts = urlsplit(url)
    if parts.password is None:
        return url
    user = parts.username or ""
    host = parts.netloc.rpartition("@")[2]
    return urlunsplit(parts._replace(netloc=f"{user}:****@{host}"))


def hide_password(text: str | None, url: str) -> str | None:
    """Network errors can quote the proxy address, password included."""
    password = urlsplit(url).password
    if text is None or not password:
        return text
    return text.replace(url, masked_url(url)).replace(password, "****")


async def list_proxies(session: AsyncSession) -> Sequence[Proxy]:
    result = await session.execute(select(Proxy).order_by(Proxy.id))
    return result.scalars().all()


async def get_proxy(session: AsyncSession, proxy_id: int) -> Proxy | None:
    return await session.get(Proxy, proxy_id)


async def save_proxy(
    session: AsyncSession, proxy: Proxy, values: ProxyCreate | ProxyUpdate
) -> Proxy:
    proxy.name = values.name
    proxy.enabled = values.enabled
    if values.url is not None and values.url != proxy.url:
        proxy.url = values.url
        # A new address: the old check result and cooldown were about another proxy.
        proxy.cooldown_until = proxy.checked_at = proxy.check_ok = None
        proxy.exit_ip = proxy.check_error = None
    session.add(proxy)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise DuplicateProxyError(f"A proxy named {values.name!r} already exists") from error
    await session.refresh(proxy)
    return proxy


async def delete_proxy(session: AsyncSession, proxy: Proxy) -> None:
    await session.delete(proxy)
    await session.commit()


def is_available(proxy: Proxy, now: datetime) -> bool:
    if not proxy.enabled:
        return False
    cooldown_until = proxy.cooldown_until
    if cooldown_until is None:
        return True
    # SQLite drops timezone info; stored values are always UTC.
    return cooldown_until.replace(tzinfo=now.tzinfo) <= now


async def start_cooldown(session: AsyncSession, proxy_id: int) -> None:
    proxy = await session.get(Proxy, proxy_id)
    if proxy is not None:
        proxy.cooldown_until = utcnow() + COOLDOWN
        await session.commit()


async def get_proxy_settings(session: AsyncSession) -> ProxySettings:
    return ProxySettings(send_cookies=await get_value(session, SEND_COOKIES) == "true")


async def set_proxy_settings(session: AsyncSession, settings: ProxySettings) -> None:
    await set_values(session, {SEND_COOKIES: "true" if settings.send_cookies else "false"})
