from datetime import UTC, datetime
from typing import Annotated
from urllib.parse import urlparse

from pydantic import AfterValidator, Field


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
