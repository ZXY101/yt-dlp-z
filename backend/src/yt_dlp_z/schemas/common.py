from datetime import UTC, datetime
from typing import Annotated, Literal, overload
from urllib.parse import urlparse

from pydantic import AfterValidator, Field


@overload
def as_utc_iso(value: datetime) -> str: ...
@overload
def as_utc_iso(value: datetime | None) -> str | None: ...
def as_utc_iso(value: datetime | None) -> str | None:
    # SQLite drops timezone info; stored values are always UTC.
    if value is None:
        return None
    return value.replace(tzinfo=value.tzinfo or UTC).isoformat()


def _web_url(url: str) -> str:
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Enter a web address starting with http:// or https://")
    return url


def _name(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValueError("Enter a name")
    return name


WebUrl = Annotated[str, Field(max_length=4096), AfterValidator(_web_url)]
Name = Annotated[str, Field(min_length=1, max_length=100), AfterValidator(_name)]

# How files are laid out (services/media_server/layout.py). Folders: one per channel,
# or per channel with a "Season YYYY" folder per year. None: straight into the folder.
FolderLayout = Literal["channel", "season"]
# File names: "Title [id]", "[20261103] Title", "[20261103] Title [id]" or a TV episode
# ("Channel - S2026E1103 - Title [id]"). None: the user's template, else yt-dlp's default.
FileNaming = Literal["title_id", "dated", "dated_id", "episode"]

# How a preset's downloads use the proxy pool (services/proxies): not at all, each
# download on the next proxy in turn, on a random one, or on the same one per channel.
ProxyMode = Literal["off", "rotate", "random", "sticky"]
