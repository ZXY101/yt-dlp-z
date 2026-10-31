from datetime import datetime
from typing import Annotated
from urllib.parse import urlsplit

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_serializer

from yt_dlp_z.schemas.common import Name, as_utc_iso

# The proxy schemes yt-dlp's --proxy understands.
PROXY_SCHEMES = {"http", "https", "socks4", "socks4a", "socks5", "socks5h"}


def _proxy_url(url: str) -> str:
    url = url.strip()
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        raise ValueError("Enter a proxy address like socks5://host:1080") from None
    if parts.scheme not in PROXY_SCHEMES or not parts.hostname or port is None:
        schemes = ", ".join(sorted(PROXY_SCHEMES))
        raise ValueError(f"Enter scheme://host:port, with one of these schemes: {schemes}")
    if parts.path.strip("/") or parts.query or parts.fragment:
        raise ValueError("A proxy address has no path: scheme://host:port")
    return url


ProxyUrl = Annotated[str, Field(max_length=2000), AfterValidator(_proxy_url)]


class ProxyCreate(BaseModel):
    name: Name
    url: ProxyUrl
    enabled: bool = True


class ProxyUpdate(BaseModel):
    name: Name
    # Left out: keep the current address (the API never returns its password).
    url: ProxyUrl | None = None
    enabled: bool = True


class ProxyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    # With any password replaced by "****".
    url: str
    enabled: bool
    cooldown_until: datetime | None
    checked_at: datetime | None
    check_ok: bool | None
    exit_ip: str | None
    check_error: str | None

    @field_serializer("cooldown_until", "checked_at")
    def as_utc(self, value: datetime | None) -> str | None:
        return as_utc_iso(value)


class ProxySettings(BaseModel):
    # Off: downloads with cookies skip the pool. One account seen from many IPs
    # can get flagged, and the cookies identify it anyway.
    send_cookies: bool = False
