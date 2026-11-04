"""Saving a video's live chat and building its overlay, through the API with the yt-dlp stub."""

import time
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest import wait_for_job
from yt_dlp_z.services.live_chat import job_step

FINISHED = {"completed", "failed", "cancelled"}
OVERLAY = {"mode": "overlay"}


def run_job(client: TestClient, video: str, live_chat: dict[str, Any] | None) -> dict[str, Any]:
    url = f"https://www.youtube.com/watch?v={video}"
    response = client.post("/api/jobs", json={"url": url, "live_chat": live_chat})
    assert response.status_code == 201
    return wait_for_job(client, response.json()["id"], FINISHED)


def wait_for_fetching(client: TestClient, job_id: int) -> None:
    deadline = time.monotonic() + 15
    while client.get(f"/api/jobs/{job_id}").json()["chat_status"] != "fetching":
        assert time.monotonic() < deadline
        time.sleep(0.05)


def job_log(client: TestClient, job_id: int) -> str:
    return client.get(f"/api/jobs/{job_id}/log").text


def test_saves_chat_and_overlay_named_like_the_video(setup_client: TestClient) -> None:
    done = run_job(setup_client, "abc", OVERLAY)
    assert done["status"] == "completed"
    assert done["chat_status"] == "overlay"
    video = Path(done["filepath"])
    assert video.with_suffix(".live_chat.json").is_file()
    overlay = video.with_suffix(".ass").read_text(encoding="utf-8-sig")
    assert "first comment" in overlay
    assert "こんにちは" in overlay
    assert "3 of 3 comments shown" in job_log(setup_client, done["id"])


def test_a_file_name_with_percent_keeps_its_name(setup_client: TestClient) -> None:
    url = "https://www.youtube.com/watch?v=abc"
    response = setup_client.post(
        "/api/jobs",
        json={"url": url, "live_chat": OVERLAY, "options": {"--output": "100%% sure.%(ext)s"}},
    )
    done = wait_for_job(setup_client, response.json()["id"], FINISHED)
    assert done["chat_status"] == "overlay"


def test_save_only_makes_no_overlay(setup_client: TestClient) -> None:
    done = run_job(setup_client, "abc", {"mode": "save"})
    assert done["chat_status"] == "saved"
    video = Path(done["filepath"])
    assert video.with_suffix(".live_chat.json").is_file()
    assert not video.with_suffix(".ass").exists()


@pytest.mark.parametrize("live_chat", [None, {"mode": "off"}])
def test_off_fetches_nothing(setup_client: TestClient, live_chat: dict[str, Any] | None) -> None:
    done = run_job(setup_client, "abc", live_chat)
    assert done["chat_status"] is None
    assert not Path(done["filepath"]).with_suffix(".live_chat.json").exists()
    assert "--write-subs" not in job_log(setup_client, done["id"])


def test_a_video_that_was_never_a_stream_is_not_asked_for_chat(setup_client: TestClient) -> None:
    done = run_job(setup_client, "plainvideo", OVERLAY)
    assert done["status"] == "completed"
    assert done["chat_status"] is None
    assert "--write-subs" not in job_log(setup_client, done["id"])


def test_a_stream_without_a_replay_says_so(setup_client: TestClient) -> None:
    done = run_job(setup_client, "nochat", OVERLAY)
    assert done["status"] == "completed"
    assert done["chat_status"] == "none"
    assert not Path(done["filepath"]).with_suffix(".ass").exists()


def test_a_failed_chat_does_not_fail_the_download(setup_client: TestClient) -> None:
    done = run_job(setup_client, "badchat", OVERLAY)
    assert done["status"] == "completed"
    assert done["error"] is None
    assert done["chat_status"] == "failed"
    assert Path(done["filepath"]).is_file()
    assert "Couldn't fetch the live chat" in job_log(setup_client, done["id"])


def test_a_failed_conversion_does_not_fail_the_download(
    setup_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(*_args: object) -> None:
        raise ValueError("strange chat")

    monkeypatch.setattr(job_step, "build_overlay", broken)
    done = run_job(setup_client, "abc", OVERLAY)
    assert done["status"] == "completed"
    assert done["chat_status"] == "failed"
    assert Path(done["filepath"]).with_suffix(".live_chat.json").is_file()


def test_a_failed_download_fetches_no_chat(setup_client: TestClient) -> None:
    done = run_job(setup_client, "failing", OVERLAY)
    assert done["status"] == "failed"
    assert done["chat_status"] is None


def test_stopping_during_the_chat_keeps_the_video(setup_client: TestClient) -> None:
    url = "https://www.youtube.com/watch?v=draggingchat"
    job = setup_client.post("/api/jobs", json={"url": url, "live_chat": OVERLAY}).json()
    wait_for_fetching(setup_client, job["id"])
    assert setup_client.post(f"/api/jobs/{job['id']}/cancel").status_code == 200
    done = wait_for_job(setup_client, job["id"], FINISHED)
    assert done["status"] == "completed"
    assert done["chat_status"] == "stopped"
    assert Path(done["filepath"]).is_file()


def test_deleting_the_download_removes_chat_and_overlay(setup_client: TestClient) -> None:
    done = run_job(setup_client, "abc", OVERLAY)
    video = Path(done["filepath"])
    response = setup_client.delete(f"/api/jobs/{done['id']}", params={"delete_files": True})
    assert response.status_code in {200, 204}
    assert not video.with_suffix(".live_chat.json").exists()
    assert not video.with_suffix(".ass").exists()


def test_rebuild_replaces_the_overlay_and_keeps_the_new_style(setup_client: TestClient) -> None:
    done = run_job(setup_client, "abc", OVERLAY)
    overlay = Path(done["filepath"]).with_suffix(".ass")
    assert "Style: Chat,Noto Sans CJK JP,48," in overlay.read_text(encoding="utf-8-sig")

    path = f"/api/jobs/{done['id']}/live-chat/overlay"
    rebuilt = setup_client.post(path, json={"font_size": 64, "colour_mode": "random"})
    assert rebuilt.status_code == 200
    assert rebuilt.json()["live_chat"]["font_size"] == 64
    assert ",64,&H" in overlay.read_text(encoding="utf-8-sig")

    # No style: the one it has now.
    assert setup_client.post(path).json()["live_chat"]["font_size"] == 64
    assert ",64,&H" in overlay.read_text(encoding="utf-8-sig")


def test_rebuild_turns_a_saved_chat_into_an_overlay(setup_client: TestClient) -> None:
    done = run_job(setup_client, "abc", {"mode": "save"})
    rebuilt = setup_client.post(f"/api/jobs/{done['id']}/live-chat/overlay")
    assert rebuilt.json()["chat_status"] == "overlay"
    assert rebuilt.json()["live_chat"]["mode"] == "overlay"
    assert Path(done["filepath"]).with_suffix(".ass").is_file()


def test_rebuild_needs_a_saved_chat(setup_client: TestClient) -> None:
    done = run_job(setup_client, "abc", None)
    response = setup_client.post(f"/api/jobs/{done['id']}/live-chat/overlay")
    assert response.status_code == 409
    assert "no saved live chat" in response.json()["detail"]


def test_rebuild_refuses_a_running_download(setup_client: TestClient) -> None:
    url = "https://www.youtube.com/watch?v=slow"
    job = setup_client.post("/api/jobs", json={"url": url, "live_chat": OVERLAY}).json()
    wait_for_job(setup_client, job["id"], {"running"})
    assert setup_client.post(f"/api/jobs/{job['id']}/live-chat/overlay").status_code == 409
    setup_client.post(f"/api/jobs/{job['id']}/cancel")


def test_rebuild_rejects_a_style_out_of_range(setup_client: TestClient) -> None:
    done = run_job(setup_client, "abc", OVERLAY)
    response = setup_client.post(f"/api/jobs/{done['id']}/live-chat/overlay", json={"opacity": 3})
    assert response.status_code == 422


def test_presets_keep_their_chat_settings(setup_client: TestClient) -> None:
    body = {"name": "Streams", "live_chat": {"mode": "overlay", "max_on_screen": 20}}
    created = setup_client.post("/api/presets", json=body)
    assert created.status_code == 201
    presets = setup_client.get("/api/presets").json()
    saved = next(preset for preset in presets if preset["name"] == "Streams")["live_chat"]
    assert saved["mode"] == "overlay"
    assert saved["max_on_screen"] == 20
    assert saved["scroll_seconds"] == 7.0
