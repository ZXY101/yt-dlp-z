from typing import Any

import pytest

from yt_dlp_z.services.notify.messages import FAILURE_STREAK
from yt_dlp_z.services.notify.notifier import Notifier
from yt_dlp_z.services.notify.ntfy import Message, NotifyError
from yt_dlp_z.services.notify.store import NtfyConfig

CONFIG = NtfyConfig(topic="downloads")


class Recorder:
    def __init__(self) -> None:
        self.sent: list[Message] = []

    async def __call__(self, _config: NtfyConfig, message: Message) -> None:
        self.sent.append(message)


def job_event(job_id: int, status: str, kind: str = "vod", **fields: Any) -> dict[str, Any]:
    job = {"id": job_id, "status": status, "kind": kind, "url": f"https://yt/{job_id}"}
    return {"type": "job", "job": {"title": f"Video {job_id}", **job, **fields}}


async def run(notifier: Notifier, *events: dict[str, Any]) -> None:
    for event in events:
        notifier.on_event(event)
    await notifier.drain()


async def test_recordings_are_announced_once() -> None:
    sent = Recorder()
    notifier = Notifier(CONFIG, sent)
    running = job_event(1, "running", "live")
    await run(notifier, running, running, running, job_event(1, "completed", "live"))
    assert [message.title for message in sent.sent] == ["Recording started", "Recording finished"]
    assert sent.sent[0].message == "Video 1"
    assert sent.sent[0].click == "https://yt/1"


async def test_downloads_starting_are_not_announced() -> None:
    sent = Recorder()
    await run(Notifier(CONFIG, sent), job_event(1, "running"), job_event(1, "cancelled"))
    assert sent.sent == []


async def test_failures_include_the_error() -> None:
    sent = Recorder()
    await run(Notifier(CONFIG, sent), job_event(1, "failed", error="Video unavailable"))
    assert sent.sent[0].title == "Download failed"
    assert sent.sent[0].message == "Video 1\nVideo unavailable"
    assert sent.sent[0].priority == 4


async def test_cookie_errors_add_a_warning() -> None:
    sent = Recorder()
    error = "ERROR: Sign in to confirm you're not a bot. Use --cookies-from-browser"
    await run(Notifier(CONFIG, sent), job_event(1, "failed", error=error))
    assert [message.title for message in sent.sent] == [
        "Download failed",
        "Cookies may have expired",
    ]


async def test_a_failure_streak_warns_once_until_a_download_works() -> None:
    sent = Recorder()
    notifier = Notifier(CONFIG, sent)
    failures = [job_event(n, "failed", error="boom") for n in range(FAILURE_STREAK + 2)]
    await run(notifier, *failures)
    assert [m.title for m in sent.sent].count("Downloads keep failing") == 1
    await run(notifier, job_event(10, "completed"), *failures[:FAILURE_STREAK])
    assert [m.title for m in sent.sent].count("Downloads keep failing") == 2


async def test_only_chosen_events_are_sent() -> None:
    sent = Recorder()
    config = NtfyConfig(topic="downloads", events=frozenset({"download_failed"}))
    await run(Notifier(config, sent), job_event(1, "completed"), job_event(2, "failed"))
    assert [message.title for message in sent.sent] == ["Download failed"]


async def test_nothing_is_sent_without_a_topic() -> None:
    sent = Recorder()
    await run(Notifier(NtfyConfig(), sent), job_event(1, "completed"))
    assert sent.sent == []


async def test_send_failures_are_logged(caplog: pytest.LogCaptureFixture) -> None:
    async def broken(_config: NtfyConfig, _message: Message) -> None:
        raise NotifyError("unreachable")

    await run(Notifier(CONFIG, broken), job_event(1, "completed"), {"type": "other"})
    assert "Notification 'Download finished' not sent: unreachable" in caplog.text
