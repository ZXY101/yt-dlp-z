"""Recordings started from the download form (POST /api/jobs with "recording")."""

from fastapi.testclient import TestClient

from tests.conftest import wait_for_job

LIVE_URL = "https://www.youtube.com/watch?v=live1"
UPCOMING_URL = "https://www.youtube.com/watch?v=upcoming1"


def test_live_stream_records_with_the_recording_settings(setup_client: TestClient) -> None:
    response = setup_client.post(
        "/api/jobs",
        json={"url": LIVE_URL, "title": "Live now", "recording": {"from_start": False}},
    )
    assert response.status_code == 201
    job = response.json()
    assert job["kind"] == "live"
    assert job["title"] == "Live now"
    assert job["record_from_start"] is False
    assert job["part_seconds"] == 6 * 3600
    assert job["max_seconds"] is None
    assert wait_for_job(setup_client, job["id"], {"running"})["status"] == "running"
    setup_client.post(f"/api/jobs/{job['id']}/cancel")


def test_upcoming_stream_waits_until_it_starts(setup_client: TestClient) -> None:
    body = {
        "url": UPCOMING_URL,
        "recording": {"from_start": True, "starts_at": "2100-01-01T00:00:00Z"},
    }
    job = setup_client.post("/api/jobs", json=body).json()
    assert job["status"] == "scheduled"
    assert job["scheduled_at"] == "2100-01-01T00:00:00+00:00"
    assert job["record_from_start"] is True


def test_plain_downloads_stay_downloads(setup_client: TestClient) -> None:
    job = setup_client.post("/api/jobs", json={"url": "https://example.com/watch/a"}).json()
    assert (job["kind"], job["title"]) == ("download", None)
