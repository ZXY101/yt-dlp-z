import sqlite3
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import wait_for_job
from tests.integration.watch_helpers import (
    CHANNEL_ID,
    subscribe,
    video_states,
    wait_for_check,
    write_feed,
)

FINISHED = {"completed", "failed", "cancelled"}


def downloaded(client: TestClient, subscription_id: int) -> dict[str, dict[str, Any]]:
    videos = client.get(f"/api/subscriptions/{subscription_id}/videos").json()
    return {video["video_id"]: wait_for_job(client, video["job_id"], FINISHED) for video in videos}


def age_all_jobs(tmp_path: Path) -> None:
    with sqlite3.connect(tmp_path / "config" / "yt-dlp-z.db") as connection:
        connection.execute("UPDATE jobs SET finished_at = '2000-01-01 00:00:00.000000'")


def sweep(client: TestClient) -> int:
    state = client.app.state.app_state  # type: ignore[attr-defined]
    result: int = client.portal.call(state.retention.sweep)  # type: ignore[union-attr]
    return result


def test_old_downloads_are_deleted_unless_kept(
    watch_client: TestClient, feeds: Path, tmp_path: Path
) -> None:
    write_feed(feeds, CHANNEL_ID, ["old1", "pinned1"])
    created = subscribe(watch_client, backfill=2, keep_days=7)
    assert created["keep_days"] == 7
    wait_for_check(watch_client, created["id"])
    jobs = downloaded(watch_client, created["id"])
    pinned = watch_client.put(f"/api/jobs/{jobs['pinned1']['id']}/keep", json={"keep": True})
    assert pinned.json()["keep"] is True

    assert sweep(watch_client) == 0  # nothing is 7 days old yet
    age_all_jobs(tmp_path)
    assert sweep(watch_client) == 1

    assert watch_client.get(f"/api/jobs/{jobs['old1']['id']}").status_code == 404
    assert not Path(jobs["old1"]["filepath"]).exists()
    assert Path(jobs["pinned1"]["filepath"]).exists()
    assert video_states(watch_client, created["id"])["old1"] == (
        "ignored",
        "Deleted 7 days after it was downloaded",
    )


def test_downloads_are_kept_by_default(
    watch_client: TestClient, feeds: Path, tmp_path: Path
) -> None:
    write_feed(feeds, CHANNEL_ID, ["forever1"])
    created = subscribe(watch_client, backfill=1)
    assert created["keep_days"] is None
    wait_for_check(watch_client, created["id"])
    jobs = downloaded(watch_client, created["id"])
    age_all_jobs(tmp_path)
    assert sweep(watch_client) == 0
    assert Path(jobs["forever1"]["filepath"]).exists()


def test_keep_days_must_be_sensible(watch_client: TestClient) -> None:
    for days in [0, -1, 100_000]:
        response = watch_client.post(
            "/api/subscriptions", json={"channel": "@demo", "keep_days": days}
        )
        assert response.status_code == 422, days
