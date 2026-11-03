"""A recording's VOD, downloaded some hours after the stream when the preset says so."""

import sqlite3
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import wait_for_job

LIVE_URL = "https://www.youtube.com/watch?v=live1"
FINISHED = {"completed", "failed", "cancelled"}


def record(client: TestClient, **recording: Any) -> dict[str, Any]:
    body = {"url": LIVE_URL, "recording": {"from_start": True, **recording}}
    response = client.post("/api/jobs", json=body)
    assert response.status_code == 201, response.text
    return wait_for_job(client, response.json()["id"], FINISHED)


def vod_of(client: TestClient, recording: dict[str, Any]) -> dict[str, Any] | None:
    jobs = client.get("/api/jobs").json()
    return next((job for job in jobs if job["source_job_id"] == recording["id"]), None)


def make_due(client: TestClient, tmp_path: Path) -> None:
    with sqlite3.connect(tmp_path / "config" / "yt-dlp-z.db") as connection:
        connection.execute(
            "UPDATE jobs SET scheduled_at = '2000-01-01 00:00:00.000000' WHERE status = 'scheduled'"
        )
    state = client.app.state.app_state  # type: ignore[attr-defined]
    client.portal.call(state.live.queue_due)  # type: ignore[union-attr]


def test_no_vod_unless_asked(setup_client: TestClient) -> None:
    recording = record(setup_client)
    assert recording["status"] == "completed"
    assert vod_of(setup_client, recording) is None


def test_the_vod_is_scheduled_and_kept_beside_the_recording(
    setup_client: TestClient, tmp_path: Path
) -> None:
    recording = record(setup_client, vod_after_hours=2)
    assert recording["vod_after_seconds"] == 2 * 3600
    vod = vod_of(setup_client, recording)
    assert vod is not None
    assert (vod["kind"], vod["status"], vod["vod_replace"]) == ("download", "scheduled", False)

    make_due(setup_client, tmp_path)
    done = wait_for_job(setup_client, vod["id"], FINISHED)
    assert done["status"] == "completed"
    assert Path(done["filepath"]).name == "Fake video live1 (VOD) [live1].mp4"
    assert Path(recording["filepath"]).exists()
    assert setup_client.get(f"/api/jobs/{recording['id']}").status_code == 200


def test_the_vod_can_replace_the_recording(setup_client: TestClient, tmp_path: Path) -> None:
    recording = record(setup_client, vod_after_hours=1, vod_replace=True)
    vod = vod_of(setup_client, recording)
    assert vod is not None
    make_due(setup_client, tmp_path)
    done = wait_for_job(setup_client, vod["id"], FINISHED)
    assert Path(done["filepath"]).exists()
    assert not Path(recording["filepath"]).exists()
    assert setup_client.get(f"/api/jobs/{recording['id']}").status_code == 404
