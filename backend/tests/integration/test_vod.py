"""A recording's VOD, downloaded some hours after the stream when the preset says so."""

import sqlite3
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest import wait_for_job
from yt_dlp_z.services.live import vod_check

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


def lengths_by_name(monkeypatch: pytest.MonkeyPatch, recording: float, vod: float) -> None:
    """The stub's files aren't real media, so ffprobe can't measure them."""

    async def fake_seconds(path: Path) -> float:
        return vod if "(VOD)" in path.name else recording

    monkeypatch.setattr(vod_check, "media_seconds", fake_seconds)


def test_the_vod_can_replace_the_recording(
    setup_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lengths_by_name(monkeypatch, recording=3600, vod=3590)
    recording = record(setup_client, vod_after_hours=1, vod_replace=True)
    vod = vod_of(setup_client, recording)
    assert vod is not None
    make_due(setup_client, tmp_path)
    done = wait_for_job(setup_client, vod["id"], FINISHED)
    assert Path(done["filepath"]).exists()
    # The VOD shows as completed first; the recording is deleted right after.
    deadline = time.monotonic() + 5
    while setup_client.get(f"/api/jobs/{recording['id']}").status_code != 404:
        assert time.monotonic() < deadline, "the recording wasn't deleted"
        time.sleep(0.05)
    assert not Path(recording["filepath"]).exists()


def kept_after_vod(client: TestClient, tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Runs a replacing VOD; returns the recording and the VOD once its note has been saved."""
    recording = record(client, vod_after_hours=1, vod_replace=True)
    vod = vod_of(client, recording)
    assert vod is not None
    make_due(client, tmp_path)
    wait_for_job(client, vod["id"], FINISHED)
    deadline = time.monotonic() + 5
    while (saved := client.get(f"/api/jobs/{vod['id']}").json())["vod_note"] is None:
        assert time.monotonic() < deadline, "the VOD has no note"
        time.sleep(0.05)
    return recording, saved


def test_a_vod_shorter_than_the_recording_keeps_the_recording(
    setup_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lengths_by_name(monkeypatch, recording=3600, vod=2880)
    recording, vod = kept_after_vod(setup_client, tmp_path)
    assert "12 min shorter" in vod["vod_note"]
    assert Path(recording["filepath"]).exists()
    assert setup_client.get(f"/api/jobs/{recording['id']}").status_code == 200
    assert "12 min shorter" in setup_client.get(f"/api/jobs/{vod['id']}/log").text


def test_lengths_that_cannot_be_compared_keep_the_recording(
    setup_client: TestClient, tmp_path: Path
) -> None:
    # The stub's files aren't media, so the real ffprobe, or none at all, can't measure them.
    recording, vod = kept_after_vod(setup_client, tmp_path)
    assert "couldn't compare" in vod["vod_note"]
    assert Path(recording["filepath"]).exists()
