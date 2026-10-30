from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import TEST_PASSWORD, MakeClient, wait_for_job

SLOW_URL = "https://example.com/watch/slow"


def update(client: TestClient, **changes: Any) -> Any:
    body = {**client.get("/api/settings").json(), **changes}
    return client.put("/api/settings", json=body)


def start(client: TestClient, url: str) -> int:
    job_id: int = client.post("/api/jobs", json={"url": url}).json()["id"]
    return job_id


def test_reads_the_setup_values_and_env_default(setup_client: TestClient, tmp_path: Path) -> None:
    assert setup_client.get("/api/settings").json() == {
        "download_dir": str((tmp_path / "downloads").resolve()),
        "max_concurrent_downloads": 3,
    }


def test_changing_the_download_folder_applies_to_new_downloads(
    setup_client: TestClient, tmp_path: Path
) -> None:
    new_dir = tmp_path / "elsewhere"
    response = update(setup_client, download_dir=str(new_dir))
    assert response.status_code == 200
    assert new_dir.is_dir()
    job = setup_client.post("/api/jobs", json={"url": "https://example.com/a"}).json()
    assert job["output_dir"] == str(new_dir.resolve())


def test_invalid_values_are_rejected(setup_client: TestClient) -> None:
    assert update(setup_client, download_dir="relative/path").status_code == 422
    assert update(setup_client, max_concurrent_downloads=0).status_code == 422
    assert update(setup_client, max_concurrent_downloads=11).status_code == 422


def test_settings_need_auth_and_setup(client: TestClient, make_client: MakeClient) -> None:
    assert client.get("/api/settings").status_code == 401
    assert make_client(auth_mode="none").get("/api/settings").status_code == 409


def test_the_download_limit_changes_while_running(setup_client: TestClient) -> None:
    update(setup_client, max_concurrent_downloads=1)
    first, second = start(setup_client, SLOW_URL), start(setup_client, SLOW_URL)
    wait_for_job(setup_client, first, {"running"})
    assert setup_client.get(f"/api/jobs/{second}").json()["status"] == "queued"

    update(setup_client, max_concurrent_downloads=2)
    wait_for_job(setup_client, second, {"running"})

    # Lowering the limit lets running downloads finish instead of stopping them.
    update(setup_client, max_concurrent_downloads=1)
    third = start(setup_client, SLOW_URL)
    assert setup_client.get(f"/api/jobs/{first}").json()["status"] == "running"
    setup_client.post(f"/api/jobs/{first}/cancel")
    assert setup_client.get(f"/api/jobs/{third}").json()["status"] == "queued"
    setup_client.post(f"/api/jobs/{second}/cancel")
    wait_for_job(setup_client, third, {"running"})
    setup_client.post(f"/api/jobs/{third}/cancel")


def test_the_download_limit_survives_a_restart(make_client: MakeClient, tmp_path: Path) -> None:
    first = make_client()
    first.post("/api/auth/setup", json={"password": TEST_PASSWORD, "download_dir": str(tmp_path)})
    update(first, max_concurrent_downloads=5)
    restarted = make_client()
    restarted.cookies.update(first.cookies)
    assert restarted.get("/api/settings").json()["max_concurrent_downloads"] == 5
