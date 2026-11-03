import time
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.conftest import MakeClient
from tests.ntfy_server import fake_ntfy
from tests.pot_server import fake_pot_server
from yt_dlp_z.services.ytdlp.global_args import global_args, set_global_args

OFF = {
    "url": None,
    "server_version": None,
    "error": None,
    "checked_at": None,
    "plugin_version": None,
}


def plugin_folder(tmp_path: Path) -> Path:
    return tmp_path / "config" / "plugins" / "bgutil"


def wait_until(client: TestClient, done: Callable[[dict[str, object]], bool]) -> dict[str, object]:
    deadline = time.monotonic() + 10
    while True:
        info: dict[str, object] = client.get("/api/ytdlp/pot").json()
        if done(info) or time.monotonic() > deadline:
            return info
        time.sleep(0.05)


def test_off_by_default(setup_client: TestClient) -> None:
    assert setup_client.get("/api/ytdlp/pot").json() == OFF
    assert global_args() == []


def test_test_reports_the_server_version(setup_client: TestClient) -> None:
    with fake_pot_server("2.0.2") as server:
        response = setup_client.post("/api/ytdlp/pot/test", json={"url": server.url})
    assert response.json() == {"server_version": "2.0.2"}
    assert setup_client.get("/api/ytdlp/pot").json() == OFF


def test_test_explains_what_is_wrong(setup_client: TestClient) -> None:
    with fake_pot_server() as server:
        gone = server.url
    response = setup_client.post("/api/ytdlp/pot/test", json={"url": gone})
    assert response.status_code == 502
    assert response.json()["detail"].startswith("Couldn't reach the provider")
    with fake_ntfy() as other:
        response = setup_client.post("/api/ytdlp/pot/test", json={"url": other.url})
    assert response.json()["detail"] == "The provider answered with error 501."
    for body in ["<html>hello</html>", '{"version": "2.0.2 --index-url x"}', "[]"]:
        with fake_pot_server() as server:
            server.body = body
            response = setup_client.post("/api/ytdlp/pot/test", json={"url": server.url})
        assert response.status_code == 502
        assert "doesn't answer like a bgutil PO token provider" in response.json()["detail"]


def test_saving_installs_the_matching_plugin(setup_client: TestClient, tmp_path: Path) -> None:
    with fake_pot_server("2.0.2") as server:
        info = setup_client.put("/api/ytdlp/pot", json={"url": server.url}).json()
    assert info["url"] == server.url
    assert info["server_version"] == "2.0.2"
    assert info["plugin_version"] == "2.0.2"
    assert info["error"] is None
    plugins = tmp_path / "config" / "plugins"
    assert (plugins / "bgutil" / "yt_dlp_plugins").is_dir()
    assert global_args() == [
        "--plugin-dirs",
        str(plugins),
        "--extractor-args",
        f"youtubepot-bgutilhttp:base_url={server.url}",
    ]


def test_an_unreachable_server_is_not_saved(setup_client: TestClient, tmp_path: Path) -> None:
    with fake_pot_server() as server:
        gone = server.url
    response = setup_client.put("/api/ytdlp/pot", json={"url": gone})
    assert response.status_code == 502
    assert setup_client.get("/api/ytdlp/pot").json() == OFF
    assert not plugin_folder(tmp_path).exists()


def test_a_failed_plugin_install_is_not_saved(
    setup_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_PIP_FAIL", "1")
    with fake_pot_server() as server:
        response = setup_client.put("/api/ytdlp/pot", json={"url": server.url})
    assert response.status_code == 502
    assert response.json()["detail"].startswith("Couldn't install the PO token plugin 1.2.3")
    assert setup_client.get("/api/ytdlp/pot").json() == OFF
    assert global_args() == []


def test_turning_off_removes_the_plugin(setup_client: TestClient, tmp_path: Path) -> None:
    with fake_pot_server() as server:
        setup_client.put("/api/ytdlp/pot", json={"url": server.url})
    assert setup_client.put("/api/ytdlp/pot", json={"url": None}).json() == OFF
    assert not plugin_folder(tmp_path).exists()
    assert global_args() == []


def test_bad_urls_are_rejected(setup_client: TestClient) -> None:
    for url in ["ftp://example.com", "not a url", ""]:
        response = setup_client.put("/api/ytdlp/pot", json={"url": url})
        assert response.status_code == 422, url


def restart(setup_client: TestClient, make_client: MakeClient) -> TestClient:
    set_global_args([])
    restarted = make_client()
    restarted.cookies = setup_client.cookies
    return restarted


def test_a_restart_keeps_the_provider(setup_client: TestClient, make_client: MakeClient) -> None:
    with fake_pot_server() as server:
        setup_client.put("/api/ytdlp/pot", json={"url": server.url})
        restarted = restart(setup_client, make_client)
        # Set before the first check, so downloads started at once get the plugin.
        assert global_args()[-1] == f"youtubepot-bgutilhttp:base_url={server.url}"
        info = wait_until(restarted, lambda info: info["server_version"] is not None)
    assert info["url"] == server.url
    assert info["error"] is None


def test_a_server_update_brings_the_matching_plugin(
    setup_client: TestClient, make_client: MakeClient
) -> None:
    with fake_pot_server("1.2.3") as server:
        setup_client.put("/api/ytdlp/pot", json={"url": server.url})
        server.version = "1.3.0"
        restarted = restart(setup_client, make_client)
        info = wait_until(restarted, lambda info: info["plugin_version"] == "1.3.0")
    assert info["server_version"] == "1.3.0"


def test_an_unreachable_server_after_a_restart_keeps_the_plugin(
    setup_client: TestClient, make_client: MakeClient
) -> None:
    with fake_pot_server() as server:
        setup_client.put("/api/ytdlp/pot", json={"url": server.url})
    restarted = restart(setup_client, make_client)
    info = wait_until(restarted, lambda info: info["error"] is not None)
    assert str(info["error"]).startswith("Couldn't reach the provider")
    assert info["plugin_version"] == "1.2.3"
    assert global_args()[-1] == f"youtubepot-bgutilhttp:base_url={server.url}"
