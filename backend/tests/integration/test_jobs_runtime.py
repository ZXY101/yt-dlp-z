import asyncio
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from tests.conftest import TEST_PASSWORD, MakeClient, wait_for_job
from yt_dlp_z.api.state import AppState
from yt_dlp_z.core.config import AuthMode, Settings
from yt_dlp_z.db.models.job import Job, JobStatus
from yt_dlp_z.main import create_app
from yt_dlp_z.services.jobs import manager as manager_module
from yt_dlp_z.services.ytdlp import schema as schema_module

FINISHED = {"completed", "failed", "cancelled"}


def test_websocket_streams_job_events(setup_client: TestClient) -> None:
    with setup_client.websocket_connect("/api/ws") as socket:
        job = setup_client.post("/api/jobs", json={"url": "https://example.com/ws"}).json()
        statuses: list[str] = []
        while not statuses or statuses[-1] not in FINISHED:
            event: dict[str, Any] = socket.receive_json()
            assert event["type"] == "job"
            assert event["job"]["id"] == job["id"]
            statuses.append(event["job"]["status"])
        setup_client.delete(f"/api/jobs/{job['id']}")
        assert socket.receive_json() == {"type": "job_deleted", "id": job["id"]}
    assert statuses[0] == "queued"
    assert "running" in statuses
    assert statuses[-1] == "completed"


def test_websocket_rejects_signed_out_and_cross_site(setup_client: TestClient) -> None:
    signed_out = TestClient(setup_client.app)
    with pytest.raises(WebSocketDisconnect) as closed, signed_out.websocket_connect("/api/ws"):
        pass
    assert closed.value.code == 4401

    headers = {"origin": "https://evil.example"}
    with (
        pytest.raises(WebSocketDisconnect),
        setup_client.websocket_connect("/api/ws", headers=headers),
    ):
        pass


def test_jobs_interrupted_by_a_restart(make_client: MakeClient, tmp_path: Path) -> None:
    first = make_client()
    first.post("/api/auth/setup", json={"password": TEST_PASSWORD, "download_dir": str(tmp_path)})
    state: AppState = first.app.state.app_state  # type: ignore[attr-defined]

    async def insert(status: JobStatus) -> int:
        async with state.session_factory() as session:
            job = Job(url="https://example.com/r", status=status, output_dir=str(tmp_path))
            session.add(job)
            await session.commit()
            return job.id

    # Written behind the manager's back to simulate rows left by a crashed process.
    running_id = asyncio.run(insert(JobStatus.RUNNING))
    queued_id = asyncio.run(insert(JobStatus.QUEUED))

    restarted = make_client()
    restarted.cookies.update(first.cookies)
    interrupted = restarted.get(f"/api/jobs/{running_id}").json()
    assert interrupted["status"] == "failed"
    assert "Interrupted" in interrupted["error"]
    assert wait_for_job(restarted, queued_id, FINISHED)["status"] == "completed"


def test_crashed_job_is_marked_failed(
    setup_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def explode(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(manager_module, "execute_job", explode)
    job = setup_client.post("/api/jobs", json={"url": "https://example.com/x"}).json()
    done = wait_for_job(setup_client, job["id"], FINISHED)
    assert done["status"] == "failed"
    assert "internal error" in done["error"]


def test_schema_failure_is_reported(
    make_client: MakeClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        schema_module, "DUMP_COMMAND", [sys.executable, "-c", "raise SystemExit(1)"]
    )
    client = make_client(auth_mode=AuthMode.NONE)
    client.post("/api/auth/setup", json={"download_dir": str(tmp_path)})

    assert client.get("/api/options/schema").status_code == 503
    assert client.post("/api/jobs", json={"url": "https://example.com/v"}).status_code == 503
    system = client.get("/api/system").json()
    assert system["ytdlp_version"] is None
    assert "Couldn't read" in system["ytdlp_error"]


def test_options_schema_and_system_info(setup_client: TestClient) -> None:
    schema = setup_client.get("/api/options/schema").json()
    flags = {option["flag"] for group in schema["groups"] for option in group["options"]}
    assert {"--format", "--extract-audio", "--exec"} <= flags
    system = setup_client.get("/api/system").json()
    assert system["ytdlp_version"] == schema["ytdlp_version"]
    assert isinstance(system["ffmpeg_available"], bool)


def test_test_reset_stops_running_jobs(setup_client: TestClient) -> None:
    job = setup_client.post("/api/jobs", json={"url": "https://example.com/slow"}).json()
    wait_for_job(setup_client, job["id"], {"running"})
    assert setup_client.post("/api/test/reset").status_code == 204
    assert setup_client.get("/api/auth/status").json()["setup_required"] is True
    state: AppState = setup_client.app.state.app_state  # type: ignore[attr-defined]
    assert not (state.settings.config_dir / "logs").exists()


def test_shutdown_stops_running_downloads(
    make_settings: Callable[..., Settings], tmp_path: Path
) -> None:
    """Regression: shutting down used to leave yt-dlp running in the background."""
    with TestClient(create_app(make_settings())) as client:
        client.post(
            "/api/auth/setup", json={"password": TEST_PASSWORD, "download_dir": str(tmp_path)}
        )
        job = client.post("/api/jobs", json={"url": "https://example.com/slow"}).json()
        wait_for_job(client, job["id"], {"running"})
        state: AppState = client.app.state.app_state  # type: ignore[attr-defined]
        pid = state.jobs.downloads._processes[job["id"]].pid

    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
