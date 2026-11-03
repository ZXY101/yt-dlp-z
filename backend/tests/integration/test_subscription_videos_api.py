from pathlib import Path
from typing import Any

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

FINISHED = {"completed", "failed", "cancelled"}


def videos_by_id(client: TestClient, subscription_id: int) -> dict[str, dict[str, Any]]:
    videos = client.get(f"/api/subscriptions/{subscription_id}/videos").json()
    return {video["video_id"]: video for video in videos}


def set_ignored(
    client: TestClient, subscription_id: int, video: dict[str, Any], ignored: bool
) -> dict[str, Any]:
    path = f"/api/subscriptions/{subscription_id}/videos/{video['id']}"
    response = client.put(path, json={"ignored": ignored})
    assert response.status_code == 200, response.text
    result: dict[str, Any] = response.json()
    return result


def test_usage_counts_what_is_on_disk_and_deleting_files_ignores_the_video(
    watch_client: TestClient, feeds: Path
) -> None:
    write_feed(feeds, CHANNEL_ID, ["first", "second"])
    created = subscribe(watch_client, backfill=2)
    wait_for_check(watch_client, created["id"])
    videos = videos_by_id(watch_client, created["id"])
    jobs = [wait_for_job(watch_client, videos[name]["job_id"], FINISHED) for name in videos]
    usage_path = f"/api/subscriptions/{created['id']}/usage"
    one_file = len(b"fake video")
    assert watch_client.get(usage_path).json() == {
        "downloads": 2,
        "files": 2,
        "bytes": 2 * one_file,
    }

    first = next(job for job in jobs if job["url"].endswith("first"))
    response = watch_client.delete(f"/api/jobs/{first['id']}", params={"delete_files": True})
    assert response.status_code == 204
    assert not Path(first["filepath"]).exists()
    assert watch_client.get(usage_path).json() == {"downloads": 1, "files": 1, "bytes": one_file}
    assert video_states(watch_client, created["id"])["first"] == (
        "ignored",
        "Its files were deleted",
    )


def test_ignored_videos_are_never_retried_until_allowed_again(
    watch_client: TestClient, feeds: Path
) -> None:
    write_feed(feeds, CHANNEL_ID, [])
    created = subscribe(watch_client)
    wait_for_check(watch_client, created["id"])
    write_feed(feeds, CHANNEL_ID, ["broken1"])
    check(watch_client, created["id"])
    broken = videos_by_id(watch_client, created["id"])["broken1"]
    assert broken["state"] == "failed"

    ignored = set_ignored(watch_client, created["id"], broken, True)
    assert (ignored["state"], ignored["reason"]) == ("ignored", "You chose not to download it")
    check(watch_client, created["id"])
    assert video_states(watch_client, created["id"])["broken1"][0] == "ignored"

    allowed = set_ignored(watch_client, created["id"], broken, False)
    assert allowed["state"] == "failed"
    check(watch_client, created["id"])
    state, reason = video_states(watch_client, created["id"])["broken1"]
    assert state == "failed"
    assert reason != "Checked again on the next check"


def test_ignoring_a_video_cancels_its_download(watch_client: TestClient, feeds: Path) -> None:
    write_feed(feeds, CHANNEL_ID, ["slow1"])
    created = subscribe(watch_client, backfill=1)
    wait_for_check(watch_client, created["id"])
    video = videos_by_id(watch_client, created["id"])["slow1"]
    wait_for_job(watch_client, video["job_id"], {"running"})
    set_ignored(watch_client, created["id"], video, True)
    assert wait_for_job(watch_client, video["job_id"], FINISHED)["status"] == "cancelled"


def test_unknown_videos_are_404(watch_client: TestClient, feeds: Path) -> None:
    write_feed(feeds, CHANNEL_ID, [])
    created = subscribe(watch_client)
    path = f"/api/subscriptions/{created['id']}/videos/999"
    assert watch_client.put(path, json={"ignored": True}).status_code == 404
    assert watch_client.get("/api/subscriptions/999/usage").status_code == 404
