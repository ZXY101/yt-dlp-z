"""Saving a recording's live chat while it records, through the API with the yt-dlp stub."""

import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from tests.conftest import wait_for_job
from tests.integration.test_live_recording import (
    FINISHED,
    app_state,
    start_recording,
    wait_for_recorded_bytes,
    watch_url,
)
from yt_dlp_z.core.config import Settings
from yt_dlp_z.db.models.job import Job
from yt_dlp_z.schemas.live_chat import LiveChatSettings
from yt_dlp_z.services.jobs import manager
from yt_dlp_z.services.jobs.context import JobContext
from yt_dlp_z.services.live_chat import capture, overlay
from yt_dlp_z.services.ytdlp.output import InfoUpdate, ProgressUpdate

OVERLAY = {"mode": "overlay"}
SAVE = {"mode": "save"}


def capture_folder(client: TestClient, job_id: int) -> Path:
    return app_state(client).settings.config_dir / "live-chat" / f"job-{job_id}"


def wait_for_comments(client: TestClient, job_id: int, wanted: int = 5) -> None:
    deadline = time.monotonic() + 15
    while True:
        files = list(capture_folder(client, job_id).glob("chat-*"))
        lines = sum(len(path.read_text(encoding="utf-8").splitlines()) for path in files)
        if lines >= wanted:
            return
        assert time.monotonic() < deadline, "the capture wrote nothing"
        time.sleep(0.05)


def stop(client: TestClient, job_id: int) -> dict[str, Any]:
    wait_for_recorded_bytes(client, job_id)
    assert client.post(f"/api/jobs/{job_id}/cancel").status_code == 200
    return wait_for_job(client, job_id, FINISHED)


def test_a_recording_saves_its_chat_beside_the_video(watch_client: TestClient) -> None:
    job_id = start_recording(watch_client, watch_url("slow-live"), live_chat=OVERLAY)
    wait_for_comments(watch_client, job_id)
    job = watch_client.get(f"/api/jobs/{job_id}").json()
    assert job["status"] == "running"
    assert job["chat_status"] == "capturing"

    done = stop(watch_client, job_id)
    assert done["chat_status"] == "overlay"
    video = Path(done["filepath"])
    assert "live comment" in video.with_suffix(".ass").read_text(encoding="utf-8-sig")
    assert '"videoOffsetTimeMsec"' in video.with_suffix(".live_chat.json").read_text("utf-8")
    assert not capture_folder(watch_client, job_id).exists()


def test_save_only_makes_no_overlay(watch_client: TestClient) -> None:
    job_id = start_recording(watch_client, watch_url("slow-live"), live_chat=SAVE)
    wait_for_comments(watch_client, job_id)
    done = stop(watch_client, job_id)
    assert done["chat_status"] == "saved"
    assert not Path(done["filepath"]).with_suffix(".ass").exists()


def test_no_setting_starts_no_capture(watch_client: TestClient) -> None:
    job_id = start_recording(watch_client, watch_url("live"))
    done = wait_for_job(watch_client, job_id, FINISHED)
    assert done["chat_status"] is None
    assert "--write-subs" not in watch_client.get(f"/api/jobs/{job_id}/log").text


def test_each_part_gets_its_own_chat_and_overlay(watch_client: TestClient) -> None:
    job_id = start_recording(
        watch_client, watch_url("slow-live"), part_seconds=2, max_seconds=4, live_chat=OVERLAY
    )
    # Two parts plus their merging, on a machine that may be busy with the rest of the suite.
    done = wait_for_job(watch_client, job_id, FINISHED, timeout=45)
    assert done["status"] == "completed"
    assert done["chat_status"] == "overlay"
    folder = Path(done["filepath"]).parent
    for part in (1, 2):
        stem = f"Fake video slow-live [slow-live] (part {part})"
        assert (folder / f"{stem}.mp4").is_file()
        assert "live comment" in (folder / f"{stem}.ass").read_text(encoding="utf-8-sig")


def test_a_stream_without_chat_does_not_touch_the_recording(
    watch_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(capture, "RETRY_SECONDS", (0.1,))
    job_id = start_recording(watch_client, watch_url("live-livechatoff"), live_chat=OVERLAY)
    done = wait_for_job(watch_client, job_id, FINISHED)
    assert done["status"] == "completed"
    assert done["error"] is None
    assert done["chat_status"] == "none"


def test_a_capture_that_dies_starts_again(
    watch_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(capture, "RETRY_SECONDS", (0.1,))
    job_id = start_recording(watch_client, watch_url("slow-livechatdies"), live_chat=SAVE)
    deadline = time.monotonic() + 15
    folder = capture_folder(watch_client, job_id)
    while len(list(folder.glob("chat-*"))) < 2:
        assert time.monotonic() < deadline, "the capture didn't start again"
        time.sleep(0.05)
    done = stop(watch_client, job_id)
    assert done["status"] == "cancelled"
    assert done["chat_status"] == "saved"


def test_a_chat_that_cannot_be_saved_does_not_fail_the_recording(
    watch_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(*_args: object) -> None:
        raise ValueError("strange chat")

    monkeypatch.setattr(capture, "build_overlay", broken)
    job_id = start_recording(watch_client, watch_url("slow-live"), live_chat=OVERLAY)
    wait_for_comments(watch_client, job_id)
    done = stop(watch_client, job_id)
    assert done["status"] == "cancelled"
    assert Path(done["filepath"]).is_file()
    assert done["chat_status"] == "failed"
    # Kept, so what was captured isn't lost, until the download is removed.
    folder = capture_folder(watch_client, job_id)
    assert list(folder.glob("chat-*"))
    assert watch_client.delete(f"/api/jobs/{job_id}").status_code in {200, 204}
    assert not folder.exists()


def test_stopping_is_answered_even_if_saving_the_chat_takes_long(
    watch_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_build = overlay.build_overlay

    def slow_build(*args: Any) -> Any:
        time.sleep(1)
        return real_build(*args)

    monkeypatch.setattr(capture, "build_overlay", slow_build)
    monkeypatch.setattr(manager, "FINISH_TIMEOUT_SECONDS", 0.1)
    job_id = start_recording(watch_client, watch_url("slow-live"), live_chat=OVERLAY)
    wait_for_comments(watch_client, job_id)
    wait_for_recorded_bytes(watch_client, job_id)
    assert watch_client.post(f"/api/jobs/{job_id}/cancel").status_code == 200
    assert wait_for_job(watch_client, job_id, FINISHED)["chat_status"] == "overlay"


def test_a_vod_keeps_the_chat_setting(watch_client: TestClient) -> None:
    job_id = start_recording(
        watch_client, watch_url("live"), live_chat=SAVE, vod_after_seconds=3600
    )
    wait_for_job(watch_client, job_id, FINISHED)
    jobs = watch_client.get("/api/jobs").json()
    vod = next(job for job in jobs if job["source_job_id"] == job_id)
    assert vod["live_chat"]["mode"] == "save"


def test_a_part_from_now_starts_where_ffmpeg_says_its_video_starts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ffmpeg joins behind the live edge, so early updates are ahead of real time; the time of
    0:00 settles at its earliest value once it's caught up."""
    job = Job(id=1, chat_capture={"parts": []}, record_from_start=False)
    settings = Settings(config_dir=tmp_path)
    context = cast(JobContext, SimpleNamespace(settings=settings))
    chat = capture.ChatCapture(context, job, LiveChatSettings(mode="save"))
    clock = [1000.0]
    monkeypatch.setattr(time, "time", lambda: clock[0])
    chat.begin_part(1)
    for now, position in [(1000.0, 8.0), (1001.0, 15.0), (1010.0, 24.0), (1020.0, 30.0)]:
        clock[0] = now
        update = ProgressUpdate(None, None, None, None, None, media_seconds=position)
        chat.on_update(1, update)
    assert job.chat_capture == {"parts": [{"part": 1, "started": 986.0, "file": None}]}


def test_a_part_from_the_stream_start_keeps_the_streams_start(tmp_path: Path) -> None:
    job = Job(id=1, chat_capture={"parts": []}, record_from_start=True)
    context = cast(JobContext, SimpleNamespace(settings=Settings(config_dir=tmp_path)))
    chat = capture.ChatCapture(context, job, LiveChatSettings(mode="save"))
    chat.begin_part(1)
    chat.on_update(1, InfoUpdate("Title", release_timestamp=500.0))
    chat.on_update(1, ProgressUpdate(None, None, None, None, None, media_seconds=3.0))
    assert job.chat_capture == {"parts": [{"part": 1, "started": 500.0, "file": None}]}
