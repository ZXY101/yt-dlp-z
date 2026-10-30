import os
import sys
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest import TEST_PASSWORD, MakeClient
from yt_dlp_z.services.ytdlp.updater import bundled_version


def wait_for_update(client: TestClient, timeout: float = 15) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while True:
        info: dict[str, Any] = client.get("/api/ytdlp").json()
        if info["update"]["state"] != "running" or time.monotonic() > deadline:
            return info
        time.sleep(0.05)


def setup(client: TestClient, tmp_path: Path) -> TestClient:
    response = client.post(
        "/api/auth/setup",
        json={"password": TEST_PASSWORD, "download_dir": str(tmp_path / "downloads")},
    )
    assert response.status_code == 204
    return client


def test_reports_the_bundled_version_before_any_update(setup_client: TestClient) -> None:
    assert setup_client.get("/api/ytdlp").json() == {
        "bundled_version": bundled_version(),
        "active_version": bundled_version(),
        "using_update": False,
        "channel": "stable",
        "update": {"state": "idle", "message": None, "finished_at": None},
    }


def test_update_installs_into_the_config_folder(setup_client: TestClient, tmp_path: Path) -> None:
    response = setup_client.post("/api/ytdlp/update")
    assert response.status_code == 202
    info = wait_for_update(setup_client)
    assert info["update"]["state"] == "succeeded"
    assert info["update"]["message"] == "Updated yt-dlp to 2099.1.1."
    assert info["update"]["finished_at"] is not None
    assert info["active_version"] == "2099.1.1"
    assert info["using_update"] is True
    update_dir = tmp_path / "config" / "ytdlp"
    assert (update_dir / "yt_dlp-2099.1.1.dist-info").is_dir()
    assert not (tmp_path / "config" / "ytdlp.new").exists()


def test_a_second_update_reports_no_newer_version(setup_client: TestClient) -> None:
    setup_client.post("/api/ytdlp/update")
    wait_for_update(setup_client)
    setup_client.post("/api/ytdlp/update")
    info = wait_for_update(setup_client)
    assert info["update"]["message"] == "yt-dlp 2099.1.1 is the newest version."


def test_nightly_channel_installs_pre_releases(setup_client: TestClient) -> None:
    response = setup_client.put("/api/ytdlp/channel", json={"channel": "nightly"})
    assert response.json()["channel"] == "nightly"
    setup_client.post("/api/ytdlp/update")
    assert wait_for_update(setup_client)["active_version"] == "2099.1.2.dev0"


def test_unknown_channel_is_rejected(setup_client: TestClient) -> None:
    response = setup_client.put("/api/ytdlp/channel", json={"channel": "beta"})
    assert response.status_code == 422


def test_failed_update_keeps_the_current_version(
    setup_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    setup_client.post("/api/ytdlp/update")
    wait_for_update(setup_client)
    monkeypatch.setenv("FAKE_PIP_FAIL", "1")
    setup_client.put("/api/ytdlp/channel", json={"channel": "nightly"})
    setup_client.post("/api/ytdlp/update")
    info = wait_for_update(setup_client)
    assert info["update"] == {
        "state": "failed",
        "message": "The update failed: ERROR: No matching distribution found for yt-dlp[default]",
        "finished_at": info["update"]["finished_at"],
    }
    assert info["active_version"] == "2099.1.1"


def test_pip_that_installs_nothing_is_a_failure(make_client: MakeClient, tmp_path: Path) -> None:
    client = setup(make_client(ytdlp_pip_command=[sys.executable, "-c", "pass"]), tmp_path)
    client.post("/api/ytdlp/update")
    info = wait_for_update(client)
    assert info["update"]["message"] == "pip finished but yt-dlp wasn't installed."
    assert info["using_update"] is False


def test_only_one_update_runs_at_a_time(make_client: MakeClient, tmp_path: Path) -> None:
    slow_pip = [sys.executable, "-c", "import time; time.sleep(2)"]
    client = setup(make_client(ytdlp_pip_command=slow_pip), tmp_path)
    assert client.post("/api/ytdlp/update").status_code == 202
    assert client.post("/api/ytdlp/update").status_code == 409
    assert client.delete("/api/ytdlp/update").status_code == 409


def test_removing_the_update_goes_back_to_the_bundled_version(
    setup_client: TestClient, tmp_path: Path
) -> None:
    setup_client.post("/api/ytdlp/update")
    wait_for_update(setup_client)
    info = setup_client.delete("/api/ytdlp/update").json()
    assert info["active_version"] == bundled_version()
    assert info["using_update"] is False
    assert not (tmp_path / "config" / "ytdlp").exists()


def test_update_folder_is_on_pythonpath_while_the_app_runs(
    make_client: MakeClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYTHONPATH", "/existing")
    client = make_client()
    update_dir = str(tmp_path / "config" / "ytdlp")
    assert os.environ["PYTHONPATH"] == os.pathsep.join([update_dir, "/existing"])
    client.__exit__(None, None, None)
    assert os.environ["PYTHONPATH"] == "/existing"


def test_requires_login(client: TestClient) -> None:
    assert client.get("/api/ytdlp").status_code == 401
    assert client.post("/api/ytdlp/update").status_code == 401
