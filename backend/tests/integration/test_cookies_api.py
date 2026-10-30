import stat
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import wait_for_job
from tests.unit.test_cookie_parse import FAKE_COOKIES

FINISHED = {"completed", "failed", "cancelled"}


def upload(client: TestClient, name: str = "YouTube", content: str = FAKE_COOKIES) -> Any:
    response = client.post("/api/cookies", json={"name": name, "content": content})
    assert response.status_code == 201, response.text
    return response.json()


def stored_file(tmp_path: Path, cookie_id: int) -> Path:
    return tmp_path / "config" / "cookies" / f"{cookie_id}.txt"


def test_upload_stores_a_private_file_and_never_returns_it(
    setup_client: TestClient, tmp_path: Path
) -> None:
    cookie = upload(setup_client)
    assert cookie["cookie_count"] == 3
    assert cookie["domains"] == ["example.com", "youtube.com"]
    assert "content" not in cookie

    path = stored_file(tmp_path, cookie["id"])
    assert path.read_text() == FAKE_COOKIES
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    listed = setup_client.get("/api/cookies").text
    assert "fake-session" not in listed


def test_rename_replace_and_delete(setup_client: TestClient, tmp_path: Path) -> None:
    cookie = upload(setup_client)
    renamed = setup_client.put(f"/api/cookies/{cookie['id']}", json={"name": "Main"}).json()
    assert renamed["name"] == "Main"
    assert renamed["cookie_count"] == 3

    one_cookie = "example.org\tFALSE\t/\tFALSE\t0\ta\tb"
    replaced = setup_client.put(
        f"/api/cookies/{cookie['id']}", json={"name": "Main", "content": one_cookie}
    ).json()
    assert replaced["cookie_count"] == 1
    assert stored_file(tmp_path, cookie["id"]).read_text() == one_cookie

    assert setup_client.delete(f"/api/cookies/{cookie['id']}").status_code == 204
    assert not stored_file(tmp_path, cookie["id"]).exists()
    assert setup_client.delete(f"/api/cookies/{cookie['id']}").status_code == 404


def test_invalid_files_and_duplicate_names_are_rejected(setup_client: TestClient) -> None:
    response = setup_client.post("/api/cookies", json={"name": "x", "content": "not cookies"})
    assert response.status_code == 422
    assert "Netscape" in response.json()["detail"]
    upload(setup_client, name="Taken")
    assert (
        setup_client.post(
            "/api/cookies", json={"name": "Taken", "content": FAKE_COOKIES}
        ).status_code
        == 409
    )
    assert setup_client.put("/api/cookies/999", json={"name": "x"}).status_code == 404
    assert (
        setup_client.post("/api/cookies/999/check", json={"url": "https://a.b"}).status_code == 404
    )


def test_check_reports_success_and_failure(setup_client: TestClient) -> None:
    cookie = upload(setup_client)
    ok = setup_client.post(
        f"/api/cookies/{cookie['id']}/check", json={"url": "https://example.com/watch/members"}
    ).json()
    assert ok == {"ok": True, "message": "Opened “Fake video members” with these cookies."}

    failed = setup_client.post(
        f"/api/cookies/{cookie['id']}/check", json={"url": "https://example.com/watch/fail"}
    ).json()
    assert failed["ok"] is False
    assert "Sign in to confirm" in failed["message"]
    bad_url = setup_client.post(f"/api/cookies/{cookie['id']}/check", json={"url": "nope"})
    assert bad_url.status_code == 422


def test_downloads_get_a_temporary_copy_of_the_cookies(
    setup_client: TestClient, tmp_path: Path
) -> None:
    cookie = upload(setup_client)
    job = setup_client.post(
        "/api/jobs", json={"url": "https://example.com/watch/abc", "cookie_id": cookie["id"]}
    ).json()
    assert job["cookie_id"] == cookie["id"]
    assert wait_for_job(setup_client, job["id"], FINISHED)["status"] == "completed"

    log = setup_client.get(f"/api/jobs/{job['id']}/log").text
    assert "--cookies" in log
    assert "[fake] cookies: 3" in log
    assert str(stored_file(tmp_path, cookie["id"])) not in log
    assert list((tmp_path / "config" / "cookies" / "running").iterdir()) == []


def test_unknown_cookie_ids_are_rejected(setup_client: TestClient) -> None:
    job = setup_client.post("/api/jobs", json={"url": "https://example.com/a", "cookie_id": 42})
    assert job.status_code == 422
    preset = setup_client.post("/api/presets", json={"name": "x", "cookie_id": 42})
    assert preset.status_code == 422


def test_deleting_cookies_unlinks_presets_and_fails_retries(setup_client: TestClient) -> None:
    cookie = upload(setup_client)
    preset = setup_client.post("/api/presets", json={"name": "x", "cookie_id": cookie["id"]}).json()
    job = setup_client.post(
        "/api/jobs", json={"url": "https://example.com/watch/fail", "cookie_id": cookie["id"]}
    ).json()
    wait_for_job(setup_client, job["id"], FINISHED)

    setup_client.delete(f"/api/cookies/{cookie['id']}")
    assert setup_client.get(f"/api/presets/{preset['id']}").json()["cookie_id"] is None
    setup_client.post(f"/api/jobs/{job['id']}/retry")
    retried = wait_for_job(setup_client, job["id"], FINISHED)
    assert retried["status"] == "failed"
    assert "cookies file for this download was deleted" in retried["error"]
