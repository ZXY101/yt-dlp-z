import asyncio
from datetime import timedelta
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
from yt_dlp_z.api.state import AppState
from yt_dlp_z.db.models.job import Job, JobKind, JobStatus, utcnow
from yt_dlp_z.db.models.video import Video, VideoState

FINISHED = {"completed", "failed", "cancelled"}
STREAMS_TOO = {"content_types": ["video", "stream"]}


def app_state(client: TestClient) -> AppState:
    state: AppState = client.app.state.app_state  # type: ignore[attr-defined]
    return state


def jobs_by_url(client: TestClient) -> dict[str, dict[str, Any]]:
    return {job["url"]: job for job in client.get("/api/jobs").json()}


def watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def insert_recording(client: TestClient, url: str, starts_in: timedelta) -> int:
    """A scheduled recording, written straight to the DB like the watcher does."""
    state = app_state(client)

    async def insert() -> int:
        async with state.session_factory() as session:
            job = Job(
                url=url,
                status=JobStatus.SCHEDULED,
                kind=JobKind.LIVE,
                scheduled_at=utcnow() + starts_in,
                output_dir=str(state.settings.config_dir),
            )
            session.add(job)
            await session.commit()
            return job.id

    return asyncio.run(insert())


def run_scheduler(client: TestClient) -> None:
    # In the app's own event loop: the scheduler hands jobs to the app's queues.
    client.portal.call(app_state(client).live.queue_due)  # type: ignore[union-attr]


def test_streams_are_recorded_instead_of_downloaded(watch_client: TestClient, feeds: Path) -> None:
    write_feed(feeds, CHANNEL_ID, [])
    created = subscribe(watch_client, filters=STREAMS_TOO)
    wait_for_check(watch_client, created["id"])
    write_feed(feeds, CHANNEL_ID, ["upcoming1", "live1", "plain"])
    check(watch_client, created["id"])

    jobs = jobs_by_url(watch_client)
    upcoming = jobs[watch_url("upcoming1")]
    assert upcoming["kind"] == "live"
    assert upcoming["status"] == "scheduled"
    assert upcoming["scheduled_at"] == "2100-01-01T00:00:00+00:00"
    assert upcoming["title"] == "Fake video upcoming1"
    assert jobs[watch_url("plain")]["kind"] == "download"

    live = wait_for_job(watch_client, jobs[watch_url("live1")]["id"], FINISHED)
    assert live["status"] == "completed"
    assert live["kind"] == "live"
    # Video (1 MB) and audio (0.1 MB) progress, added up.
    assert live["downloaded_bytes"] == 1_100_000
    log = watch_client.get(f"/api/jobs/{live['id']}/log").text
    assert "--live-from-start --wait-for-video 30-300" in log

    states = video_states(watch_client, created["id"])
    assert states["upcoming1"] == ("upcoming", None)
    assert states["live1"] == ("live", None)


def test_streams_seen_before_recording_existed_get_a_recording(
    watch_client: TestClient, feeds: Path
) -> None:
    write_feed(feeds, CHANNEL_ID, [])
    created = subscribe(watch_client, filters=STREAMS_TOO)
    wait_for_check(watch_client, created["id"])
    state = app_state(watch_client)

    async def insert_old_row() -> None:
        async with state.session_factory() as session:
            video = Video(
                subscription_id=created["id"],
                video_id="upcoming1",
                title="Old row",
                state=VideoState.UPCOMING,
                live_status="is_upcoming",
            )
            session.add(video)
            await session.commit()

    asyncio.run(insert_old_row())
    write_feed(feeds, CHANNEL_ID, ["upcoming1"])
    check(watch_client, created["id"])
    assert jobs_by_url(watch_client)[watch_url("upcoming1")]["status"] == "scheduled"


def test_the_scheduler_starts_recordings_shortly_before_the_stream(
    watch_client: TestClient,
) -> None:
    soon = insert_recording(watch_client, watch_url("upcoming-soon"), timedelta(minutes=2))
    later = insert_recording(watch_client, watch_url("upcoming-later"), timedelta(hours=2))
    run_scheduler(watch_client)

    recorded = wait_for_job(watch_client, soon, FINISHED)
    assert recorded["status"] == "completed"
    log = watch_client.get(f"/api/jobs/{soon}/log").text
    assert "Waiting for the stream to start" in log
    assert watch_client.get(f"/api/jobs/{later}").json()["status"] == "scheduled"


def test_a_scheduled_recording_can_be_cancelled(watch_client: TestClient) -> None:
    job_id = insert_recording(watch_client, watch_url("upcoming1"), timedelta(hours=2))
    response = watch_client.post(f"/api/jobs/{job_id}/cancel")
    assert response.json()["status"] == "cancelled"
    run_scheduler(watch_client)
    assert watch_client.get(f"/api/jobs/{job_id}").json()["status"] == "cancelled"


def test_recordings_do_not_wait_behind_downloads(watch_client: TestClient) -> None:
    body = watch_client.get("/api/settings").json()
    watch_client.put("/api/settings", json={**body, "max_concurrent_downloads": 1})
    slow = watch_client.post("/api/jobs", json={"url": "https://example.com/slow"}).json()
    waiting = watch_client.post("/api/jobs", json={"url": "https://example.com/quick"}).json()
    wait_for_job(watch_client, slow["id"], {"running"})

    recording = insert_recording(watch_client, watch_url("live-now"), timedelta(0))
    run_scheduler(watch_client)
    assert wait_for_job(watch_client, recording, FINISHED)["status"] == "completed"
    assert watch_client.get(f"/api/jobs/{waiting['id']}").json()["status"] == "queued"
    watch_client.post(f"/api/jobs/{slow['id']}/cancel")


def test_the_streams_tab_catches_streams_the_feed_missed(
    watch_client: TestClient, feeds: Path
) -> None:
    write_feed(feeds, "UCstreamer", [])
    created = subscribe(watch_client, channel="@streamer", backfill=5, filters=STREAMS_TOO)
    wait_for_check(watch_client, created["id"])

    states = video_states(watch_client, created["id"])
    assert states["live-tab1"] == ("live", None)
    assert states["ended-tab1"] == ("skipped", "Found on the streams tab after it ended")
    assert jobs_by_url(watch_client)[watch_url("live-tab1")]["kind"] == "live"


def test_the_streams_tab_is_left_alone_without_the_stream_filter(
    watch_client: TestClient, feeds: Path
) -> None:
    write_feed(feeds, "UCstreamer", [])
    created = subscribe(watch_client, channel="@streamer", backfill=5)
    wait_for_check(watch_client, created["id"])
    assert video_states(watch_client, created["id"]) == {}


def test_a_failing_streams_tab_does_not_fail_the_check(
    watch_client: TestClient, feeds: Path
) -> None:
    write_feed(feeds, "UCbrokenstreams", ["plain"])
    created = subscribe(watch_client, channel="@brokenstreams", backfill=5, filters=STREAMS_TOO)
    checked = wait_for_check(watch_client, created["id"])
    assert checked["last_error"] is None
    assert video_states(watch_client, created["id"]) == {"plain": ("queued", None)}
