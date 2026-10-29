from pathlib import Path

from tests.conftest import MakeClient

ENV_PASSWORD = "env-pw"  # noqa: S105  (test fixture, deliberately short)


def setup_body(tmp_path: Path, password: str | None) -> dict[str, str | None]:
    return {"password": password, "download_dir": str(tmp_path / "downloads")}


def test_status_reports_env_password(make_client: MakeClient) -> None:
    client = make_client(admin_password=ENV_PASSWORD)
    assert client.get("/api/auth/status").json()["password_from_env"] is True


def test_setup_requires_the_env_password(make_client: MakeClient, tmp_path: Path) -> None:
    client = make_client(admin_password=ENV_PASSWORD)
    missing = client.post("/api/auth/setup", json={"download_dir": str(tmp_path)})
    wrong = client.post("/api/auth/setup", json=setup_body(tmp_path, "guess"))
    assert missing.status_code == 422
    assert wrong.status_code == 401
    assert client.get("/api/auth/status").json()["setup_required"] is True

    assert (
        client.post("/api/auth/setup", json=setup_body(tmp_path, ENV_PASSWORD)).status_code == 204
    )
    assert client.get("/api/auth/status").json()["authenticated"] is True


def test_wrong_env_password_during_setup_is_rate_limited(
    make_client: MakeClient, tmp_path: Path
) -> None:
    client = make_client(admin_password=ENV_PASSWORD)
    for _ in range(5):
        client.post("/api/auth/setup", json=setup_body(tmp_path, "guess"))
    response = client.post("/api/auth/setup", json=setup_body(tmp_path, ENV_PASSWORD))
    assert response.status_code == 429


def test_changing_the_env_password_rotates_it(make_client: MakeClient, tmp_path: Path) -> None:
    first = make_client(admin_password=ENV_PASSWORD)
    first.post("/api/auth/setup", json=setup_body(tmp_path, ENV_PASSWORD))
    cookies = dict(first.cookies)

    unchanged = make_client(admin_password=ENV_PASSWORD)
    unchanged.cookies.update(cookies)
    assert unchanged.get("/api/auth/status").json()["authenticated"] is True

    rotated = make_client(admin_password="new-env-password")  # noqa: S106  (test fixture)
    rotated.cookies.update(cookies)
    assert rotated.get("/api/auth/status").json()["authenticated"] is False
    assert rotated.post("/api/auth/login", json={"password": ENV_PASSWORD}).status_code == 401
    assert rotated.post("/api/auth/login", json={"password": "new-env-password"}).status_code == 204


def test_short_password_rejected_when_creating_one(make_client: MakeClient, tmp_path: Path) -> None:
    client = make_client()
    response = client.post("/api/auth/setup", json=setup_body(tmp_path, "short"))
    assert response.status_code == 422
    assert "at least 8" in response.json()["detail"]


def test_test_reset_reapplies_env_password(make_client: MakeClient, tmp_path: Path) -> None:
    client = make_client(admin_password=ENV_PASSWORD)
    client.post("/api/auth/setup", json=setup_body(tmp_path, ENV_PASSWORD))
    assert client.post("/api/test/reset").status_code == 204
    assert (
        client.post("/api/auth/setup", json=setup_body(tmp_path, ENV_PASSWORD)).status_code == 204
    )
