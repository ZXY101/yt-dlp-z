from typing import Annotated, Literal

from pydantic import BaseModel, Field

from yt_dlp_z.schemas.common import WebUrl

NotifyEvent = Literal["recording_started", "download_finished", "download_failed", "problems"]
ALL_EVENTS: list[NotifyEvent] = [
    "recording_started",
    "download_finished",
    "download_failed",
    "problems",
]
DEFAULT_SERVER = "https://ntfy.sh"

# ntfy's own rule for topic names. Empty turns notifications off.
Topic = Annotated[str, Field(max_length=64, pattern=r"^[-_A-Za-z0-9]*$")]


class NotificationSettingsIn(BaseModel):
    server: WebUrl = DEFAULT_SERVER
    topic: Topic = ""
    events: list[NotifyEvent] = Field(default_factory=lambda: list(ALL_EVENTS))
    # Access token for a protected topic. Left out keeps the saved one; "" removes it.
    token: Annotated[str, Field(max_length=256)] | None = None


class NotificationSettingsOut(BaseModel):
    server: str
    topic: str
    events: list[NotifyEvent]
    # The token itself is never sent back.
    has_token: bool
