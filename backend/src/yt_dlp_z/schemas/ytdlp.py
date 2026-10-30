from datetime import datetime
from typing import Literal

from pydantic import BaseModel

YtdlpChannel = Literal["stable", "nightly"]
UpdateState = Literal["idle", "running", "succeeded", "failed"]


class UpdateStatus(BaseModel):
    """How the last update since the app started went."""

    state: UpdateState
    message: str | None = None
    finished_at: datetime | None = None


class YtdlpPreferences(BaseModel):
    channel: YtdlpChannel
    # Install new versions found by the daily check.
    auto_update: bool


class YtdlpInfo(YtdlpPreferences):
    bundled_version: str
    # The version new yt-dlp runs use: an installed update, else the bundled one.
    active_version: str
    using_update: bool
    update: UpdateStatus
    # The newest version for the channel, from the last check since the app started.
    latest_version: str | None
    checked_at: datetime | None
