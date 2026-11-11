import time
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest import MakeClient

FAKE_COOKIES = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tSID\tfake-value\n"


def link(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def start(client: TestClient, *ids: str, **extra: object) -> str:
    response = client.post("/api/align", json={"urls": [link(i) for i in ids], **extra})
    assert response.status_code == 202, response.text
    align_id: str = response.json()["id"]
    return align_id


def wait_until_finished(client: TestClient, align_id: str, timeout: float = 30) -> Any:
    deadline = time.monotonic() + timeout
    while True:
        body = client.get(f"/api/align/{align_id}").json()
        if body["state"] in {"done", "failed"}:
            return body
        if time.monotonic() > deadline:
            raise AssertionError(f"alignment stuck in {body['state']}")
        time.sleep(0.05)


def align_dir(tmp_path: Path) -> Path:
    return tmp_path / "config" / "align"


def test_finds_offsets_and_deletes_the_audio(setup_client: TestClient, tmp_path: Path) -> None:
    align_id = start(setup_client, "align-60", "align-30", "align-120")
    body = wait_until_finished(setup_client, align_id)
    assert body["state"] == "done"
    assert body["progress"] == 1.0
    assert body["error"] is None
    offsets = body["offsets"]
    assert offsets[link("align-60")] == 0.0
    assert offsets[link("align-30")] == pytest.approx(30.0, abs=0.01)
    assert offsets[link("align-120")] == pytest.approx(-60.0, abs=0.01)
    assert body["confidence"][link("align-30")] >= 0.5
    assert [stream["stage"] for stream in body["streams"]] == ["ready"] * 3
    assert list(align_dir(tmp_path).iterdir()) == []


def test_unrelated_audio_has_no_offset(setup_client: TestClient) -> None:
    body = wait_until_finished(setup_client, start(setup_client, "align-60", "unrelated"))
    assert body["state"] == "done"
    assert body["offsets"][link("unrelated")] is None
    assert body["confidence"][link("unrelated")] < 0.5


@pytest.mark.parametrize(
    ("video_id", "message"),
    [
        ("live-now", "Only ended streams and videos up to 12 hours"),
        ("fail1", "This video is unavailable"),
        ("nodecode", "ffmpeg couldn't read the audio"),
    ],
)
def test_failures_report_why(setup_client: TestClient, video_id: str, message: str) -> None:
    body = wait_until_finished(setup_client, start(setup_client, "align-60", video_id))
    assert body["state"] == "failed"
    assert message in body["error"]


def test_one_alignment_at_a_time_and_delete_stops_it(
    setup_client: TestClient, tmp_path: Path
) -> None:
    running = start(setup_client, "align-slow", "align-30")
    time.sleep(0.5)
    body = setup_client.get(f"/api/align/{running}").json()
    assert body["state"] == "downloading"
    assert 0 < body["progress"] < 0.9
    slow, quick = body["streams"]
    assert slow["url"] == link("align-slow")
    assert slow["stage"] == "downloading"
    assert 0 < slow["downloaded"] < 1
    assert quick["stage"] in {"converting", "ready"}
    busy = setup_client.post("/api/align", json={"urls": [link("a"), link("b")]})
    assert busy.status_code == 409
    assert setup_client.delete(f"/api/align/{running}").status_code == 204
    assert not (align_dir(tmp_path) / running).exists()
    assert setup_client.get(f"/api/align/{running}").status_code == 404
    assert setup_client.delete(f"/api/align/{running}").status_code == 404
    start(setup_client, "align-60", "align-30")


def test_uses_the_chosen_cookies(setup_client: TestClient) -> None:
    cookie = setup_client.post("/api/cookies", json={"name": "YT", "content": FAKE_COOKIES})
    cookie_id = cookie.json()["id"]
    align_id = start(setup_client, "align-60", "align-30", cookie_id=cookie_id)
    assert wait_until_finished(setup_client, align_id)["state"] == "done"


@pytest.mark.parametrize(
    "body",
    [
        {"urls": [link("one")]},
        {"urls": [link(str(i)) for i in range(5)]},
        {"urls": [link("same"), link("same")]},
        {"urls": ["not a link", link("b")]},
        {"urls": [link("a"), link("b")], "cookie_id": 999},
    ],
)
def test_bad_requests_are_rejected(setup_client: TestClient, body: dict[str, object]) -> None:
    assert setup_client.post("/api/align", json=body).status_code == 422


def test_needs_auth(client: TestClient) -> None:
    assert client.post("/api/align", json={"urls": [link("a"), link("b")]}).status_code == 401
    assert client.get("/api/align/anything").status_code == 401


def test_leftover_audio_is_wiped_at_startup(make_client: MakeClient, tmp_path: Path) -> None:
    leftover = align_dir(tmp_path) / "old-job" / "audio-0.pcm"
    leftover.parent.mkdir(parents=True)
    leftover.write_bytes(b"old")
    make_client()
    assert not leftover.exists()
