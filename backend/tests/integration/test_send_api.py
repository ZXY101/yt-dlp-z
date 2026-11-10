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


def jobs_for(client: TestClient, url: str, **extra: object) -> list[dict[str, Any]]:
    response = client.post("/api/jobs/for-link", json={"url": url, **extra})
    assert response.status_code == 200
    jobs: list[dict[str, Any]] = response.json()["jobs"]
    return jobs


def test_a_links_jobs_are_found_however_it_is_written(setup_client: TestClient) -> None:
    _, sent = send(setup_client, "https://www.youtube.com/watch?v=abc")
    found = jobs_for(setup_client, "https://youtu.be/abc?si=share")
    assert [job["id"] for job in found] == [sent["job"]["id"]]
    assert found[0]["title"] == "Fake video abc"
    assert "filepath" not in found[0]
    assert "options" not in found[0]
    assert jobs_for(setup_client, "https://www.youtube.com/watch?v=other") == []


def test_a_video_and_its_playlist_have_separate_jobs(setup_client: TestClient) -> None:
    url = "https://www.youtube.com/watch?v=abc&list=PLtest"
    _, whole = send(setup_client, url, whole_playlist=True)
    assert jobs_for(setup_client, url) == []
    found = jobs_for(setup_client, url, whole_playlist=True)
    assert [job["id"] for job in found] == [whole["job"]["id"]]


def test_sending_the_same_link_twice_queues_it_once(setup_client: TestClient) -> None:
    _, first = send(setup_client, "https://www.youtube.com/watch?v=abc")
    status, again = send(setup_client, "https://youtu.be/abc?si=share")
    assert status == 201
    assert again["existing"] is True
    assert again["job"]["id"] == first["job"]["id"]
    assert len(setup_client.get("/api/jobs").json()) == 1


def test_another_preset_is_another_download(setup_client: TestClient) -> None:
    audio = preset_named(setup_client, "Audio", options={"--extract-audio": True})
    _, first = send(setup_client, "https://www.youtube.com/watch?v=abc")
    _, other = send(setup_client, "https://www.youtube.com/watch?v=abc", preset_id=audio["id"])
    assert other["existing"] is False
    assert other["job"]["id"] != first["job"]["id"]
