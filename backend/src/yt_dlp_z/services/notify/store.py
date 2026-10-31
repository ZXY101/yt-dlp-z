"""ntfy settings, kept in the settings table."""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.schemas.notifications import (
    ALL_EVENTS,
    DEFAULT_SERVER,
    NotificationSettingsIn,
    NotificationSettingsOut,
    NotifyEvent,
)
from yt_dlp_z.services.settings_store import get_value, set_values

SERVER = "ntfy_server"
TOPIC = "ntfy_topic"
TOKEN = "ntfy_token"  # noqa: S105  (a settings key, not a secret)
EVENTS = "ntfy_events"


@dataclass(frozen=True)
class NtfyConfig:
    server: str = DEFAULT_SERVER
    topic: str = ""
    token: str = ""
    events: frozenset[NotifyEvent] = frozenset(ALL_EVENTS)

    @property
    def enabled(self) -> bool:
        return bool(self.topic)

    def public(self) -> NotificationSettingsOut:
        events = [event for event in ALL_EVENTS if event in self.events]
        return NotificationSettingsOut(
            server=self.server, topic=self.topic, events=events, has_token=bool(self.token)
        )


def _events(value: str | None) -> frozenset[NotifyEvent]:
    if value is None:
        return frozenset(ALL_EVENTS)
    return frozenset(event for event in ALL_EVENTS if event in value.split(","))


async def load_config(session: AsyncSession) -> NtfyConfig:
    return NtfyConfig(
        server=await get_value(session, SERVER) or DEFAULT_SERVER,
        topic=await get_value(session, TOPIC) or "",
        token=await get_value(session, TOKEN) or "",
        events=_events(await get_value(session, EVENTS)),
    )


def merge_config(saved: NtfyConfig, body: NotificationSettingsIn) -> NtfyConfig:
    """The new settings; a token left out keeps the saved one."""
    token = saved.token if body.token is None else body.token.strip()
    return NtfyConfig(body.server, body.topic, token, frozenset(body.events))


async def save_config(session: AsyncSession, config: NtfyConfig) -> None:
    await set_values(
        session,
        {
            SERVER: config.server,
            TOPIC: config.topic,
            TOKEN: config.token,
            EVENTS: ",".join(event for event in ALL_EVENTS if event in config.events),
        },
    )
