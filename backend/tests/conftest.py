import sys
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from yt_dlp_z.core.config import AuthMode, Settings
from yt_dlp_z.main import create_app

FAKE_YTDLP = Path(__file__).resolve().parents[2] / "e2e" / "stub" / "fake_yt_dlp.py"
TEST_PASSWORD = "correct-horse-battery"  # noqa: S105  (test fixture, not a real secret)

MakeClient = Callable[..., TestClient]


@pytest.fixture
def frontend_dist(tmp_path: Path) -> Path:
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>app</html>")
    (dist / "assets" / "app.js").write_text("console.log('app')")
    return dist


@pytest.fixture
def make_settings(tmp_path: Path, frontend_dist: Path) -> Callable[..., Settings]:
    def build(**overrides: object) -> Settings:
        values: dict[str, object] = {
            "config_dir": tmp_path / "config",
            "default_download_dir": tmp_path / "downloads",
            "frontend_dist": frontend_dist,
            "auth_mode": AuthMode.PASSWORD,
            "test_mode": True,
            "ytdlp_command": [sys.executable, str(FAKE_YTDLP)],
        }
        values.update(overrides)
        return Settings.model_validate(values)

    return build


@pytest.fixture
def make_client(make_settings: Callable[..., Settings]) -> Iterator[MakeClient]:
    clients: list[TestClient] = []

    def build(**overrides: object) -> TestClient:
        client = TestClient(create_app(make_settings(**overrides)))
        client.__enter__()
        clients.append(client)
        return client

    yield build
    for client in clients:
        client.__exit__(None, None, None)


@pytest.fixture
def client(make_client: MakeClient) -> TestClient:
    return make_client()


@pytest.fixture
def setup_client(client: TestClient, tmp_path: Path) -> TestClient:
    response = client.post(
        "/api/auth/setup",
        json={"password": TEST_PASSWORD, "download_dir": str(tmp_path / "downloads")},
    )
    assert response.status_code == 204
    return client


def wait_for_job(
    client: TestClient, job_id: int, statuses: set[str], timeout: float = 15
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while True:
        job: dict[str, Any] = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in statuses:
            return job
        if time.monotonic() > deadline:
            raise AssertionError(f"job {job_id} stuck in {job['status']}, wanted {statuses}")
        time.sleep(0.05)
