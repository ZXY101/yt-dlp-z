from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest import TEST_PASSWORD, MakeClient, wait_for_job
from yt_dlp_z.services.jobs import process

FINISHED = {"completed", "failed", "cancelled"}


def start(client: TestClient, url: str, **body: Any) -> dict[str, Any]:
    response = client.post("/api/jobs", json={"url": url, **body})
    assert response.status_code == 201, response.text
    job: dict[str, Any] = response.json()
    return job


def test_download_completes(setup_client: TestClient, tmp_path: Path) -> None:
    job = start(setup_client, "https://example.com/watch/abc", options={"--embed-metadata": True})
    assert job["status"] in {"queued", "running"}

    done = wait_for_job(setup_client, job["id"], FINISHED)
    assert done["status"] == "completed"
    assert done["title"] == "Fake video abc"
    assert done["progress"] == 100
    assert Path(done["filepath"]).read_bytes() == b"fake video"
    assert Path(done["filepath"]).parent == (tmp_path / "downloads").resolve()

    log = setup_client.get(f"/api/jobs/{job['id']}/log").text
    assert "--embed-metadata" in log
    assert "[fake] done" in log
    assert not any(line.startswith("[ytdlpz:") for line in log.splitlines())


def test_failed_download_reports_the_error(setup_client: TestClient) -> None:
    job = start(setup_client, "https://example.com/fail")
    done = wait_for_job(setup_client, job["id"], FINISHED)
    assert done["status"] == "failed"
    assert done["error"] == "[fake] This video is unavailable"


def test_cancel_running_and_retry(setup_client: TestClient) -> None:
    job = start(setup_client, "https://example.com/slow")
    wait_for_job(setup_client, job["id"], {"running"})
    response = setup_client.post(f"/api/jobs/{job['id']}/cancel")
    assert response.status_code == 200
    assert wait_for_job(setup_client, job["id"], FINISHED)["status"] == "cancelled"
    assert setup_client.post(f"/api/jobs/{job['id']}/cancel").status_code == 409

    retried = setup_client.post(f"/api/jobs/{job['id']}/retry").json()
    assert retried["status"] == "queued"
    assert retried["error"] is None
    wait_for_job(setup_client, job["id"], {"running"})
    setup_client.post(f"/api/jobs/{job['id']}/cancel")
    wait_for_job(setup_client, job["id"], FINISHED)


def test_stubborn_process_is_force_killed(
    setup_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(process, "KILL_AFTER_SECONDS", 0.3)
    job = start(setup_client, "https://example.com/stubborn")
    wait_for_job(setup_client, job["id"], {"running"})
    setup_client.post(f"/api/jobs/{job['id']}/cancel")
    assert wait_for_job(setup_client, job["id"], FINISHED, timeout=5)["status"] == "cancelled"


def test_queued_job_can_be_cancelled(make_client: MakeClient, tmp_path: Path) -> None:
    client = make_client(max_concurrent_downloads=1)
    client.post(
        "/api/auth/setup", json={"password": TEST_PASSWORD, "download_dir": str(tmp_path / "d")}
    )
    blocker = start(client, "https://example.com/slow")
    waiting = start(client, "https://example.com/next")
    wait_for_job(client, blocker["id"], {"running"})
    assert client.get(f"/api/jobs/{waiting['id']}").json()["status"] == "queued"

    assert client.post(f"/api/jobs/{waiting['id']}/cancel").json()["status"] == "cancelled"
    client.post(f"/api/jobs/{blocker['id']}/cancel")
    wait_for_job(client, blocker["id"], FINISHED)
    assert client.get(f"/api/jobs/{waiting['id']}").json()["status"] == "cancelled"


def test_retry_only_for_failed_or_cancelled(setup_client: TestClient) -> None:
    job = start(setup_client, "https://example.com/ok")
    wait_for_job(setup_client, job["id"], FINISHED)
    assert setup_client.post(f"/api/jobs/{job['id']}/retry").status_code == 409


def test_delete_keeps_running_jobs(setup_client: TestClient) -> None:
    running = start(setup_client, "https://example.com/slow")
    wait_for_job(setup_client, running["id"], {"running"})
    assert setup_client.delete(f"/api/jobs/{running['id']}").status_code == 409
    setup_client.post(f"/api/jobs/{running['id']}/cancel")
    wait_for_job(setup_client, running["id"], FINISHED)

    assert setup_client.delete(f"/api/jobs/{running['id']}").status_code == 204
    assert setup_client.get(f"/api/jobs/{running['id']}").status_code == 404
    assert setup_client.get(f"/api/jobs/{running['id']}/log").status_code == 404


def test_list_is_newest_first(setup_client: TestClient) -> None:
    first = start(setup_client, "https://example.com/one")
    second = start(setup_client, "https://example.com/two")
    ids = [job["id"] for job in setup_client.get("/api/jobs").json()]
    assert ids[:2] == [second["id"], first["id"]]


def test_relative_output_dir_is_inside_the_download_folder(
    setup_client: TestClient, tmp_path: Path
) -> None:
    job = start(setup_client, "https://example.com/v", output_dir="music")
    assert job["output_dir"] == str((tmp_path / "downloads" / "music").resolve())


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ({"url": "ftp://example.com/v"}, "http"),
        ({"url": "file:///etc/passwd"}, "http"),
        ({"url": "https://e.com/v", "options": {"--nope": True}}, "Unknown yt-dlp option"),
        ({"url": "https://e.com/v", "options": {"--exec": "id"}}, "isn't allowed"),
        ({"url": "https://e.com/v", "extra_args": "--paths /tmp"}, "isn't allowed"),
        ({"url": "https://e.com/v", "output_dir": "/etc"}, "must be inside"),
        ({"url": "https://e.com/v", "output_dir": "../up"}, "must be inside"),
    ],
)
def test_invalid_requests_are_rejected(
    setup_client: TestClient, body: dict[str, Any], message: str
) -> None:
    response = setup_client.post("/api/jobs", json=body)
    assert response.status_code == 422
    assert message in response.text


def test_missing_job_is_404(setup_client: TestClient) -> None:
    assert setup_client.get("/api/jobs/999").status_code == 404
    assert setup_client.post("/api/jobs/999/cancel").status_code == 404


def test_requires_setup_and_auth(client: TestClient) -> None:
    for method, path in [("get", "/api/jobs"), ("post", "/api/jobs"), ("get", "/api/system")]:
        assert getattr(client, method)(path).status_code == 401
    no_setup = TestClient(client.app)
    assert no_setup.get("/api/options/schema").status_code == 401
