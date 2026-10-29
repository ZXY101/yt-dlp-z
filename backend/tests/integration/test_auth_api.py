import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import TEST_PASSWORD, MakeClient
from yt_dlp_z.api.state import AppState
from yt_dlp_z.core.config import AuthMode
from yt_dlp_z.services.auth_service import change_password


def test_status_before_setup(client: TestClient) -> None:
    body = client.get("/api/auth/status").json()
    assert body["setup_required"] is True
    assert body["authenticated"] is False
    assert body["auth_mode"] == "password"


def test_setup_signs_in_and_creates_folder(client: TestClient, tmp_path: Path) -> None:
    folder = tmp_path / "chosen"
    response = client.post(
        "/api/auth/setup", json={"password": TEST_PASSWORD, "download_dir": str(folder)}
    )
    assert response.status_code == 204
    assert folder.is_dir()
    body = client.get("/api/auth/status").json()
    assert body == body | {"setup_required": False, "authenticated": True}


def test_setup_only_runs_once(setup_client: TestClient, tmp_path: Path) -> None:
    response = setup_client.post(
        "/api/auth/setup", json={"password": TEST_PASSWORD, "download_dir": str(tmp_path)}
    )
    assert response.status_code == 409


def test_setup_validation(client: TestClient, tmp_path: Path) -> None:
    no_password = client.post("/api/auth/setup", json={"download_dir": str(tmp_path)})
    short = client.post("/api/auth/setup", json={"password": "short", "download_dir": "/x"})
    relative = client.post(
        "/api/auth/setup", json={"password": TEST_PASSWORD, "download_dir": "relative"}
    )
    assert [no_password.status_code, short.status_code, relative.status_code] == [422] * 3
    assert "absolute" in relative.json()["detail"]


def test_login_logout_flow(setup_client: TestClient) -> None:
    setup_client.post("/api/auth/logout")
    assert setup_client.get("/api/auth/status").json()["authenticated"] is False
    assert setup_client.post("/api/auth/login", json={"password": "nope"}).status_code == 401
    assert setup_client.post("/api/auth/login", json={"password": TEST_PASSWORD}).status_code == 204
    assert setup_client.get("/api/auth/status").json()["authenticated"] is True


def test_login_is_rate_limited(setup_client: TestClient) -> None:
    for _ in range(5):
        setup_client.post("/api/auth/login", json={"password": "nope"})
    response = setup_client.post("/api/auth/login", json={"password": TEST_PASSWORD})
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0


def test_password_change_logs_out_existing_sessions(setup_client: TestClient) -> None:
    state: AppState = setup_client.app.state.app_state  # type: ignore[attr-defined]

    async def change() -> None:
        async with state.session_factory() as session:
            await change_password(session, "another-password")

    asyncio.run(change())
    assert setup_client.get("/api/auth/status").json()["authenticated"] is False


def test_auth_mode_none_needs_no_password(make_client: MakeClient, tmp_path: Path) -> None:
    client = make_client(auth_mode=AuthMode.NONE)
    assert client.get("/api/auth/status").json()["authenticated"] is True
    response = client.post("/api/auth/setup", json={"download_dir": str(tmp_path / "d")})
    assert response.status_code == 204


def test_login_fails_when_no_password_exists(make_client: MakeClient) -> None:
    client = make_client(auth_mode=AuthMode.NONE)
    assert client.post("/api/auth/login", json={"password": "anything"}).status_code == 401
