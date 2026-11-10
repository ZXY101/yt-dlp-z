from typing import Any

import pytest
from fastapi.testclient import TestClient

from yt_dlp_z.api.routes import media
from yt_dlp_z.services.ytdlp.media import probe_media


def send(client: TestClient, url: str, **extra: object) -> tuple[int, dict[str, Any]]:
    response = client.post("/api/jobs/send", json={"url": url, **extra})
    return response.status_code, response.json()


def preset_named(client: TestClient, name: str, **fields: object) -> dict[str, Any]:
    response = client.post("/api/presets", json={"name": name, "kind": "any"} | fields)
    assert response.status_code == 201
    preset: dict[str, Any] = response.json()
    return preset


def test_a_video_uses_the_default_preset_for_videos(setup_client: TestClient) -> None:
    preset_named(setup_client, "Videos", kind="video", is_default=True)
    status, body = send(setup_client, "https://www.youtube.com/watch?v=abc")
    assert status == 201
    assert body["preset"] == "Videos"
    assert body["job"]["title"] == "Fake video abc"
    assert body["job"]["kind"] == "download"


def test_a_chosen_preset_is_applied(setup_client: TestClient) -> None:
    preset = preset_named(setup_client, "Audio", options={"--extract-audio": True})
    status, body = send(setup_client, "https://www.youtube.com/watch?v=abc", preset_id=preset["id"])
    assert status == 201
    assert body["preset"] == "Audio"
    assert body["job"]["options"]["--extract-audio"] is True


def test_an_unknown_preset_is_refused(setup_client: TestClient) -> None:
    status, body = send(setup_client, "https://www.youtube.com/watch?v=abc", preset_id=999)
    assert status == 422
    assert body["detail"] == "That preset doesn't exist"
    assert setup_client.get("/api/jobs").json() == []


def test_a_playlist_needs_whole_playlist(setup_client: TestClient) -> None:
    url = "https://www.youtube.com/playlist?list=PLtest"
    status, body = send(setup_client, url)
    assert status == 422
    assert "whole_playlist" in body["detail"]
    assert setup_client.get("/api/jobs").json() == []
    assert send(setup_client, url, whole_playlist=True)[0] == 201


def test_a_video_opened_from_a_playlist_downloads_alone(setup_client: TestClient) -> None:
    url = "https://www.youtube.com/watch?v=abc&list=PLtest"
    _, alone = send(setup_client, url)
    _, whole = send(setup_client, url, whole_playlist=True)
    assert alone["job"]["options"]["--no-playlist"] is True
    assert whole["job"]["options"]["--yes-playlist"] is True


def test_an_upcoming_stream_is_scheduled_as_a_recording(setup_client: TestClient) -> None:
    status, body = send(setup_client, "https://www.youtube.com/watch?v=upcoming1")
    assert status == 201
    assert body["job"]["kind"] == "live"
    assert body["job"]["status"] == "scheduled"


def test_a_broken_link_reports_the_ytdlp_error(setup_client: TestClient) -> None:
    status, body = send(setup_client, "https://www.youtube.com/watch?v=broken1")
    assert status == 422
    assert body["detail"] == "This video is unavailable"


def test_a_link_checked_just_before_is_not_checked_again(
    setup_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    async def counting_probe(*args: Any, **kwargs: Any) -> dict[str, Any]:
        calls.append(args[1])
        return await probe_media(*args, **kwargs)

    monkeypatch.setattr(media, "probe_media", counting_probe)
    url = "https://www.youtube.com/watch?v=abc"
    assert setup_client.post("/api/media/probe", json={"url": url}).status_code == 200
    assert send(setup_client, url)[0] == 201
    assert calls == [url]
