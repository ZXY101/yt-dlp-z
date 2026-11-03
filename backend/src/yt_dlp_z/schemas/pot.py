from datetime import datetime

from pydantic import BaseModel

from yt_dlp_z.schemas.common import WebUrl


class PotProviderIn(BaseModel):
    # The bgutil server, e.g. http://bgutil-provider:4416. None turns PO tokens off.
    url: WebUrl | None = None


class PotTestIn(BaseModel):
    url: WebUrl


class PotTestResult(BaseModel):
    server_version: str


class PotProviderInfo(BaseModel):
    url: str | None
    # From the last check of the server: its version, or why it couldn't be used.
    server_version: str | None
    error: str | None
    checked_at: datetime | None
    # The plugin installed for yt-dlp; it matches the server's version.
    plugin_version: str | None
