import time
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

CHANNEL = "@demo"
CHANNEL_ID = "UCdemo"  # what the fake yt-dlp resolves @demo to


def write_feed(feeds: Path, channel_id: str, video_ids: list[str]) -> None:
    """A YouTube-style Atom feed, newest first."""
    entries = "".join(
        f"<entry><yt:videoId>{video_id}</yt:videoId><title>Feed {video_id}</title>"
        f"<published>2026-10-{len(video_ids) - index:02d}T12:00:00+00:00</published></entry>"
        for index, video_id in enumerate(video_ids)
    )
    feeds.mkdir(exist_ok=True)
    (feeds / f"{channel_id}.xml").write_text(
        '<feed xmlns="http://www.w3.org/2005/Atom" '
        f'xmlns:yt="http://www.youtube.com/xml/schemas/2015">{entries}</feed>'
    )


def subscribe(client: TestClient, **body: Any) -> dict[str, Any]:
    response = client.post("/api/subscriptions", json={"channel": CHANNEL, **body})
    assert response.status_code == 201, response.text
    subscription: dict[str, Any] = response.json()
    return subscription


def wait_for_check(client: TestClient, subscription_id: int, timeout: float = 15) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while True:
        subscription: dict[str, Any] = client.get(f"/api/subscriptions/{subscription_id}").json()
        if not subscription["checking"]:
            return subscription
        if time.monotonic() > deadline:
            raise AssertionError(f"subscription {subscription_id} is still checking")
        time.sleep(0.05)


def check(client: TestClient, subscription_id: int) -> dict[str, Any]:
    assert client.post(f"/api/subscriptions/{subscription_id}/check").status_code == 202
    return wait_for_check(client, subscription_id)


def video_states(client: TestClient, subscription_id: int) -> dict[str, tuple[str, str | None]]:
    videos = client.get(f"/api/subscriptions/{subscription_id}/videos").json()
    return {video["video_id"]: (video["state"], video["reason"]) for video in videos}
