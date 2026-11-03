import pytest
from fastapi.testclient import TestClient

from tests.integration.watch_helpers import check, video_states, wait_for_check

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLkaraoke"


def test_a_playlist_link_watches_the_playlist(
    watch_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    response = watch_client.post(
        "/api/subscriptions", json={"channel": PLAYLIST_URL, "backfill": 1}
    )
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["kind"] == "playlist"
    assert created["channel_id"] == "PLkaraoke"
    assert created["name"] == "Fake playlist PLkaraoke"
    assert created["url"] == PLAYLIST_URL

    wait_for_check(watch_client, created["id"])
    # New videos are added at the end: the last one counts as the newest.
    states = video_states(watch_client, created["id"])
    assert states["item3"][0] == "queued"
    assert states["item1"][0] == states["item2"][0] == "skipped"

    monkeypatch.setenv("FAKE_PLAYLIST_SIZE", "4")
    check(watch_client, created["id"])
    assert video_states(watch_client, created["id"])["item4"][0] == "queued"


def test_a_video_opened_from_a_playlist_watches_the_playlist(watch_client: TestClient) -> None:
    link = "https://www.youtube.com/watch?v=abc&list=PLseries"
    created = watch_client.post("/api/subscriptions", json={"channel": link}).json()
    assert (created["kind"], created["channel_id"]) == ("playlist", "PLseries")


def test_mixes_and_broken_playlists_are_refused(watch_client: TestClient) -> None:
    mix = watch_client.post(
        "/api/subscriptions", json={"channel": "https://www.youtube.com/watch?v=a&list=RDabc"}
    )
    assert mix.status_code == 422
    assert "Mixes" in mix.json()["detail"]
    broken = watch_client.post(
        "/api/subscriptions",
        json={"channel": "https://www.youtube.com/playlist?list=PLbroken"},
    )
    assert broken.status_code == 422
    assert "Couldn't open that playlist" in broken.json()["detail"]
