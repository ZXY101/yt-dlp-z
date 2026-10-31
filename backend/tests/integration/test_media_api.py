from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import TEST_PASSWORD, MakeClient
from yt_dlp_z.api.routes.media import ERROR_PREFIX

COOKIES = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tSID\tfake-value\n"


def probe(client: TestClient, url: str, **extra: object) -> tuple[int, dict[str, object]]:
    response = client.post("/api/media/probe", json={"url": url, **extra})
    return response.status_code, response.json()


def test_video(setup_client: TestClient) -> None:
    status, body = probe(setup_client, "https://www.youtube.com/watch?v=abc")
    assert status == 200
    assert body["kind"] == "video"
    assert body["title"] == "Fake video abc"
    assert body["uploader"] == "Fake channel"
    assert body["site"] == "youtube.com"
    assert body["duration"] == 300


def test_playlist_and_the_video_in_it(setup_client: TestClient) -> None:
    url = "https://www.youtube.com/watch?v=inlist&list=PLfake"
    _, playlist = probe(setup_client, url)
    _, video = probe(setup_client, url, no_playlist=True)
    assert (playlist["kind"], playlist["entry_count"]) == ("playlist", 24)
    assert (video["kind"], video["title"]) == ("video", "Fake video inlist")


def test_channel(setup_client: TestClient) -> None:
    _, body = probe(setup_client, "https://www.youtube.com/@someone")
    assert (body["kind"], body["entry_count"]) == ("channel", 3)


def test_upcoming_and_live_streams(setup_client: TestClient) -> None:
    _, upcoming = probe(setup_client, "https://www.youtube.com/watch?v=upcoming1")
    _, live = probe(setup_client, "https://www.youtube.com/watch?v=live-old1")
    assert upcoming["kind"] == "upcoming"
    assert upcoming["starts_at"] == "2100-01-01T00:00:00Z"
    assert live["kind"] == "live"
    assert live["live_since"] is not None


def test_failure_reports_the_ytdlp_error(setup_client: TestClient) -> None:
    status, body = probe(setup_client, "https://www.youtube.com/watch?v=broken1")
    assert status == 422
    assert body["detail"] == "This video is unavailable"


def test_members_only_asks_for_cookies(setup_client: TestClient) -> None:
    status, body = probe(setup_client, "https://www.youtube.com/watch?v=members1")
    assert status == 422
    assert "Choose a cookies file" in str(body["detail"])


def test_members_only_opens_with_cookies(setup_client: TestClient) -> None:
    upload = setup_client.post("/api/cookies", json={"name": "Member", "content": COOKIES})
    url = "https://www.youtube.com/watch?v=members1"
    status, body = probe(setup_client, url, cookie_id=upload.json()["id"])
    assert status == 200
    assert body["members_only"] is True


def test_unknown_cookies_and_bad_links_are_rejected(setup_client: TestClient) -> None:
    status, _ = probe(setup_client, "https://www.youtube.com/watch?v=abc", cookie_id=999)
    assert status == 422
    status, _ = probe(setup_client, "not a link")
    assert status == 422


def test_requires_login(make_client: MakeClient, tmp_path: Path) -> None:
    client = make_client()
    client.post(
        "/api/auth/setup",
        json={"password": TEST_PASSWORD, "download_dir": str(tmp_path / "downloads")},
    )
    client.post("/api/auth/logout")
    status, _ = probe(client, "https://www.youtube.com/watch?v=abc")
    assert status == 401


def test_error_prefix_is_dropped() -> None:
    assert ERROR_PREFIX.sub("", "[youtube] dQw4w9WgXcQ: Video unavailable") == "Video unavailable"
    assert ERROR_PREFIX.sub("", "[generic] Unsupported URL: https://x.example") == (
        "Unsupported URL: https://x.example"
    )


def test_full_check_answers_when_the_fast_path_fails(setup_client: TestClient) -> None:
    status, body = probe(setup_client, "https://www.youtube.com/watch?v=fastfail1")
    assert (status, body["title"]) == (200, "Fake video fastfail1")
