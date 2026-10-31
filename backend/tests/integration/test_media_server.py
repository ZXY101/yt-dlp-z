"""Media-server output (services/media_server) from presets, downloads and subscriptions."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.conftest import wait_for_job
from tests.integration.watch_helpers import CHANNEL_ID, subscribe, wait_for_check, write_feed
from yt_dlp_z.services.jobs import job_run


def nfo_text(path: Path, tag: str) -> str | None:
    return ET.parse(path).getroot().findtext(tag)  # noqa: S314  (written by the app)


FINISHED = {"completed", "failed", "cancelled"}


def test_season_layout_saves_a_show_folder(setup_client: TestClient, tmp_path: Path) -> None:
    response = setup_client.post(
        "/api/jobs",
        json={
            "url": "https://www.youtube.com/watch?v=abc",
            "options": {"--output": "%(title)s.%(ext)s"},
            "media_layout": "season",
        },
    )
    assert response.status_code == 201
    assert response.json()["media_layout"] == "season"
    done = wait_for_job(setup_client, response.json()["id"], FINISHED)
    assert done["status"] == "completed"

    show = (tmp_path / "downloads" / "Fake channel").resolve()
    video = Path(done["filepath"])
    assert video == show / "Season 2026" / "Fake channel - S2026E1001 - Fake video abc [abc].mp4"
    assert video.with_suffix(".jpg").exists()
    assert nfo_text(video.with_suffix(".nfo"), "episode") == "1001"
    assert nfo_text(show / "tvshow.nfo", "title") == "Fake channel"


def test_nfo_write_errors_dont_fail_the_download(
    setup_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(*_args: object) -> None:
        raise PermissionError("read-only")

    monkeypatch.setattr(job_run, "write_nfo_files", broken)
    response = setup_client.post(
        "/api/jobs",
        json={"url": "https://www.youtube.com/watch?v=ro", "media_layout": "flat"},
    )
    done = wait_for_job(setup_client, response.json()["id"], FINISHED)
    assert done["status"] == "completed"


def test_presets_keep_the_layout(setup_client: TestClient) -> None:
    created = setup_client.post(
        "/api/presets", json={"name": "Jellyfin", "media_layout": "flat"}
    ).json()
    assert created["media_layout"] == "flat"
    bad = setup_client.post("/api/presets", json={"name": "Bad", "media_layout": "nested"})
    assert bad.status_code == 422
    plain = setup_client.post("/api/presets", json={"name": "Plain"}).json()
    assert plain["media_layout"] is None


def test_subscriptions_copy_the_presets_layout(watch_client: TestClient, feeds: Path) -> None:
    preset = watch_client.post(
        "/api/presets", json={"name": "Shows", "media_layout": "season"}
    ).json()
    write_feed(feeds, CHANNEL_ID, ["show"])
    created = subscribe(watch_client, backfill=1, preset_id=preset["id"])
    wait_for_check(watch_client, created["id"])
    job = watch_client.get("/api/jobs").json()[0]
    assert job["media_layout"] == "season"
