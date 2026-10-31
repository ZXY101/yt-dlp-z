"""Sends messages to an ntfy server."""

import asyncio
import json
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field

from yt_dlp_z.services.notify.store import NtfyConfig

TIMEOUT_SECONDS = 10
# ntfy's priorities: 3 is the default, 4 is "high".
HIGH_PRIORITY = 4
MESSAGE_LIMIT = 1000


class NotifyError(Exception):
    """The message couldn't be sent. The text is shown to the user."""


@dataclass(frozen=True)
class Message:
    title: str
    message: str
    tags: list[str] = field(default_factory=list)
    priority: int = 3
    # Opened when the notification is tapped.
    click: str | None = None


def _request(config: NtfyConfig, message: Message) -> urllib.request.Request:
    # JSON publishing, unlike headers, takes any text (titles in Japanese, emoji).
    body = {key: value for key, value in asdict(message).items() if value is not None}
    body["message"] = message.message[:MESSAGE_LIMIT]
    headers = {"Content-Type": "application/json"}
    if config.token:
        headers["Authorization"] = f"Bearer {config.token}"
    return urllib.request.Request(  # noqa: S310  (the server is a checked http(s) URL)
        config.server.rstrip("/"),
        data=json.dumps({"topic": config.topic, **body}).encode(),
        headers=headers,
        method="POST",
    )


def _post(request: urllib.request.Request) -> None:
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS):  # noqa: S310
            pass
    except urllib.error.HTTPError as error:
        if error.code in {401, 403}:
            raise NotifyError("The ntfy server refused the access token.") from error
        raise NotifyError(f"The ntfy server answered with error {error.code}.") from error
    except (urllib.error.URLError, OSError) as error:
        reason = getattr(error, "reason", error)
        raise NotifyError(f"Couldn't reach the ntfy server: {reason}") from error


async def send_ntfy(config: NtfyConfig, message: Message) -> None:
    await asyncio.to_thread(_post, _request(config, message))
