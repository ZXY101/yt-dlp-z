from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import wait_for_job
from tests.integration.watch_helpers import (
    CHANNEL_ID,
    check,
    subscribe,
    video_states,
    wait_for_check,
    write_feed,
)

BEFORE = "Uploaded before you subscribed"
COOKIES = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tFAKE\tnot-a-real-value\n"


def test_first_check_downloads_only_the_backfill(watch_client: TestClient, feeds: Path) -> None:
    write_feed(feeds, CHANNEL_ID, ["new", "older", "oldest"])
    created = subscribe(watch_client, backfill=1)
    assert created["channel_id"] == CHANNEL_ID
    assert created["name"] == "Fake demo"
    assert created["url"] == f"https://www.youtube.com/channel/{CHANNEL_ID}"

    subscription = wait_for_check(watch_client, created["id"])
    assert subscription["last_checked_at"] is not None
    assert subscription["last_error"] is None
    states = video_states(watch_client, created["id"])
    assert states == {
        "new": ("queued", None),
        "older": ("skipped", BEFORE),
        "oldest": ("skipped", BEFORE),
    }
    videos = watch_client.get(f"/api/subscriptions/{created['id']}/videos").json()
    assert videos[0]["title"] == "Fake video new"  # the probe's title replaces the feed's
    job = wait_for_job(watch_client, videos[0]["job_id"], {"completed"})
    assert job["url"] == "https://www.youtube.com/watch?v=new"
    assert job["subscription_id"] == created["id"]

    # The subscriptions page lists what each channel downloaded; one-off downloads don't count.
    watch_client.post("/api/jobs", json={"url": "https://example.com/watch/other"})
    mine = watch_client.get("/api/jobs", params={"subscription_id": created["id"]}).json()
    assert [item["id"] for item in mine] == [job["id"]]
    other = watch_client.get("/api/jobs", params={"subscription_id": created["id"] + 1}).json()
    assert other == []


def test_later_checks_filter_each_new_video(watch_client: TestClient, feeds: Path) -> None:
    write_feed(feeds, CHANNEL_ID, ["old"])
    filters = {"content_types": ["video", "stream"], "max_duration": 3600}
    created = subscribe(watch_client, filters=filters)
    wait_for_check(watch_client, created["id"])
    new = ["plain", "short1", "upcoming1", "live1", "members1", "broken1", "long1"]
    write_feed(feeds, CHANNEL_ID, [*new, "old"])

    check(watch_client, created["id"])
    states = video_states(watch_client, created["id"])
    assert states["old"] == ("skipped", BEFORE)
    assert states["plain"] == ("queued", None)
    assert states["short1"] == ("skipped", "It's a Short")
    assert states["upcoming1"] == ("upcoming", None)
    assert states["live1"] == ("live", None)
    assert states["members1"] == ("skipped", "Members-only")
    assert states["broken1"][0] == "failed"
    assert "unavailable" in (states["broken1"][1] or "")
    assert states["long1"] == ("skipped", "Longer than the maximum duration")
    videos = watch_client.get(f"/api/subscriptions/{created['id']}/videos").json()
    upcoming = next(video for video in videos if video["video_id"] == "upcoming1")
    assert upcoming["release_at"] == "2100-01-01T00:00:00+00:00"


def test_failed_videos_are_retried_and_queued_ones_are_not(
    watch_client: TestClient, feeds: Path
) -> None:
    write_feed(feeds, CHANNEL_ID, [])
    created = subscribe(watch_client)
    wait_for_check(watch_client, created["id"])
    write_feed(feeds, CHANNEL_ID, ["broken1", "plain"])
    check(watch_client, created["id"])
    check(watch_client, created["id"])
    videos = watch_client.get(f"/api/subscriptions/{created['id']}/videos").json()
    assert sorted(video["video_id"] for video in videos) == ["broken1", "plain"]
    jobs = watch_client.get("/api/jobs").json()
    assert [job["url"] for job in jobs] == ["https://www.youtube.com/watch?v=plain"]


def test_members_only_videos_can_be_included(watch_client: TestClient, feeds: Path) -> None:
    write_feed(feeds, CHANNEL_ID, ["members1"])
    created = subscribe(watch_client, backfill=1, filters={"include_members_only": True})
    wait_for_check(watch_client, created["id"])
    # Without a member's cookies yt-dlp can't open it, so it fails instead of being skipped.
    assert video_states(watch_client, created["id"])["members1"][0] == "failed"


def test_members_only_videos_open_with_the_presets_cookies(
    watch_client: TestClient, feeds: Path
) -> None:
    cookies = watch_client.post("/api/cookies", json={"name": "Member", "content": COOKIES}).json()
    preset = watch_client.post("/api/presets", json={"name": "M", "cookie_id": cookies["id"]})
    write_feed(feeds, CHANNEL_ID, ["members1"])
    filters = {"include_members_only": True}
    created = subscribe(watch_client, backfill=1, filters=filters, preset_id=preset.json()["id"])
    wait_for_check(watch_client, created["id"])
    assert video_states(watch_client, created["id"])["members1"] == ("queued", None)
    assert watch_client.get("/api/jobs").json()[0]["cookie_id"] == cookies["id"]


def test_the_preset_and_folder_shape_the_download(watch_client: TestClient, feeds: Path) -> None:
    preset = watch_client.post(
        "/api/presets",
        json={"name": "Audio", "options": {"--extract-audio": True}, "output_dir": "music"},
    ).json()
    write_feed(feeds, CHANNEL_ID, ["plain"])
    created = subscribe(watch_client, backfill=1, preset_id=preset["id"], output_dir="channel")
    wait_for_check(watch_client, created["id"])
    job = watch_client.get("/api/jobs").json()[0]
    assert job["options"] == {"--extract-audio": True}
    assert job["output_dir"].endswith("/downloads/channel")


def test_the_videos_tab_stands_in_for_a_missing_feed(watch_client: TestClient) -> None:
    created = subscribe(watch_client, channel="@uploader", backfill=1)
    subscription = wait_for_check(watch_client, created["id"])
    assert subscription["last_error"] is None
    assert subscription["last_checked_at"] is not None
    assert video_states(watch_client, created["id"]) == {
        "tab-new": ("queued", None),
        "tab-old": ("skipped", BEFORE),
    }
    videos = watch_client.get(f"/api/subscriptions/{created['id']}/videos").json()
    # The tab has no dates; the probe's upload time fills it in.
    assert videos[0]["published_at"].startswith("2026-10-01T12:00:00")


def test_a_broken_feed_is_reported(watch_client: TestClient, feeds: Path) -> None:
    created = subscribe(watch_client, channel="@broken")
    subscription = wait_for_check(watch_client, created["id"])
    assert subscription["last_checked_at"] is None
    error = subscription["last_error"]
    assert "Couldn't load the channel feed" in error
    assert "The videos tab failed too: [fake] This channel has no videos tab" in error

    feeds.mkdir()
    (feeds / "UCbroken.xml").write_text("<feed>")
    assert "isn't valid XML" in check(watch_client, created["id"])["last_error"]


def test_paused_subscriptions_are_not_checked_on_creation(watch_client: TestClient) -> None:
    created = subscribe(watch_client, enabled=False)
    assert created["checking"] is False
    assert created["enabled"] is False
