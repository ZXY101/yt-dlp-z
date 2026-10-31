from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import wait_for_job
from tests.integration.test_cookies_api import upload

FINISHED = {"completed", "failed", "cancelled"}
PASSWORD = "fake-proxy-secret"  # noqa: S105  (test fixture, not a real secret)


def add_proxy(client: TestClient, name: str, url: str, **body: Any) -> dict[str, Any]:
    response = client.post("/api/proxies", json={"name": name, "url": url, **body})
    assert response.status_code == 201, response.text
    proxy: dict[str, Any] = response.json()
    return proxy


def run_job(client: TestClient, url: str = "https://example.com/v", **body: Any) -> dict[str, Any]:
    response = client.post("/api/jobs", json={"url": url, "proxy_mode": "rotate", **body})
    assert response.status_code == 201, response.text
    return wait_for_job(client, response.json()["id"], FINISHED)


def log_of(client: TestClient, job_id: int) -> str:
    return client.get(f"/api/jobs/{job_id}/log").text


def test_create_list_update_and_delete(setup_client: TestClient) -> None:
    proxy = add_proxy(setup_client, "VPN 1", f"socks5://me:{PASSWORD}@vpn-1:1080")
    assert proxy["url"] == "socks5://me:****@vpn-1:1080"
    assert proxy["enabled"] is True
    assert PASSWORD not in setup_client.get("/api/proxies").text

    duplicate = setup_client.post("/api/proxies", json={"name": "VPN 1", "url": "http://x:8888"})
    assert duplicate.status_code == 409

    # Without a url the address (and its password) stays.
    renamed = setup_client.put(
        f"/api/proxies/{proxy['id']}", json={"name": "Home VPN", "enabled": False}
    ).json()
    assert renamed["name"] == "Home VPN"
    assert renamed["enabled"] is False
    assert renamed["url"] == "socks5://me:****@vpn-1:1080"

    moved = setup_client.put(
        f"/api/proxies/{proxy['id']}", json={"name": "Home VPN", "url": "http://vpn-2:8888"}
    ).json()
    assert moved["url"] == "http://vpn-2:8888"

    assert setup_client.delete(f"/api/proxies/{proxy['id']}").status_code == 204
    assert setup_client.get("/api/proxies").json() == []
    assert setup_client.delete(f"/api/proxies/{proxy['id']}").status_code == 404
    assert setup_client.put(f"/api/proxies/{proxy['id']}", json={"name": "x"}).status_code == 404


def test_rejects_addresses_yt_dlp_cant_use(setup_client: TestClient) -> None:
    for url in ["vpn:1080", "ftp://vpn:21", "socks5://vpn", "http://vpn:8888/path", "http://:80"]:
        response = setup_client.post("/api/proxies", json={"name": "Bad", "url": url})
        assert response.status_code == 422, url


def test_settings(setup_client: TestClient) -> None:
    assert setup_client.get("/api/proxies/settings").json() == {"send_cookies": False}
    saved = setup_client.put("/api/proxies/settings", json={"send_cookies": True})
    assert saved.json() == {"send_cookies": True}
    assert setup_client.get("/api/proxies/settings").json() == {"send_cookies": True}


def test_check_reports_the_exit_ip_or_the_error(setup_client: TestClient) -> None:
    good = add_proxy(setup_client, "Good", "http://vpn-1:8888")
    checked = setup_client.post(f"/api/proxies/{good['id']}/check").json()
    assert checked["check_ok"] is True
    assert checked["exit_ip"] == "203.0.113.7 (ZZ)"
    assert checked["checked_at"] is not None

    dead = add_proxy(setup_client, "Dead", f"socks5://me:{PASSWORD}@dead:1080")
    failed = setup_client.post(f"/api/proxies/{dead['id']}/check").json()
    assert failed["check_ok"] is False
    assert failed["check_error"] == "Unable to connect to proxy socks5://me:****@dead:1080"

    garbage = add_proxy(setup_client, "Garbage", "http://garbage:8888")
    broken = setup_client.post(f"/api/proxies/{garbage['id']}/check").json()
    assert broken["check_error"] == "The proxy check exited with code 0."
    assert setup_client.post("/api/proxies/999/check").status_code == 404


def test_jobs_rotate_through_the_pool(setup_client: TestClient) -> None:
    first = add_proxy(setup_client, "A", "http://vpn-a:8888")
    second = add_proxy(setup_client, "B", "http://vpn-b:8888")
    jobs = [run_job(setup_client), run_job(setup_client), run_job(setup_client)]
    assert [job["status"] for job in jobs] == ["completed"] * 3
    assert [job["proxy_id"] for job in jobs] == [first["id"], second["id"], first["id"]]
    assert "--proxy http://vpn-a:8888" in log_of(setup_client, jobs[0]["id"])

    direct = run_job(setup_client, proxy_mode="off")
    assert direct["proxy_id"] is None
    assert "--proxy" not in log_of(setup_client, direct["id"])


def test_a_blocked_proxy_cools_down_and_the_next_one_tries(setup_client: TestClient) -> None:
    blocked = add_proxy(setup_client, "Blocked", "http://blocked:8888")
    good = add_proxy(setup_client, "Good", "http://vpn-1:8888")
    job = run_job(setup_client)
    assert job["status"] == "completed"
    assert job["proxy_id"] == good["id"]
    assert "The proxy was blocked or didn't connect; trying the next one." in log_of(
        setup_client, job["id"]
    )

    proxies = {proxy["id"]: proxy for proxy in setup_client.get("/api/proxies").json()}
    assert proxies[blocked["id"]]["cooldown_until"] is not None
    assert proxies[good["id"]]["cooldown_until"] is None
    # Cooling down: the next job skips it.
    assert run_job(setup_client)["proxy_id"] == good["id"]

    # A check that works ends the cooldown early.
    setup_client.put(f"/api/proxies/{blocked['id']}", json={"name": "Blocked", "enabled": True})
    checked = setup_client.post(f"/api/proxies/{blocked['id']}/check").json()
    assert checked["cooldown_until"] is None


def test_fails_when_every_proxy_is_blocked(setup_client: TestClient) -> None:
    add_proxy(setup_client, "Blocked 1", "http://blocked-1:8888")
    add_proxy(setup_client, "Blocked 2", f"http://me:{PASSWORD}@blocked-2:8888")
    job = run_job(setup_client)
    assert job["status"] == "failed"
    assert job["error"] == (
        "Every proxy this download tried was blocked or didn't connect. Retry it later."
    )
    again = run_job(setup_client)
    assert (
        again["error"]
        == "Every proxy is cooling down after being blocked or not connecting. Retry later."
    )


def test_fails_rather_than_going_direct(setup_client: TestClient) -> None:
    empty = run_job(setup_client)
    assert empty["status"] == "failed"
    assert empty["error"] == (
        "This preset uses the proxy pool, but no proxy is turned on (Settings → Proxies)."
    )
    add_proxy(setup_client, "Off", "http://vpn-1:8888", enabled=False)
    assert run_job(setup_client)["status"] == "failed"


def test_downloads_with_cookies_skip_the_pool_unless_allowed(setup_client: TestClient) -> None:
    proxy = add_proxy(setup_client, "A", "http://vpn-a:8888")
    cookie = upload(setup_client)
    assert run_job(setup_client, cookie_id=cookie["id"])["proxy_id"] is None

    setup_client.put("/api/proxies/settings", json={"send_cookies": True})
    assert run_job(setup_client, cookie_id=cookie["id"])["proxy_id"] == proxy["id"]


def test_a_recording_blocked_through_a_proxy_cools_it_down(setup_client: TestClient) -> None:
    blocked = add_proxy(setup_client, "Blocked", "http://blocked:8888")
    add_proxy(setup_client, "Good", "http://vpn-1:8888")
    job = run_job(
        setup_client,
        url="https://www.youtube.com/watch?v=live1",
        recording={"from_start": True},
    )
    # Recordings aren't retried: a restart would lose what the stream already showed.
    assert job["status"] == "failed"
    assert job["proxy_id"] == blocked["id"]
    assert "not a bot" in job["error"]
    proxies = setup_client.get("/api/proxies").json()
    assert proxies[0]["cooldown_until"] is not None


def test_presets_keep_their_proxy_mode(setup_client: TestClient) -> None:
    created = setup_client.post("/api/presets", json={"name": "Hidden", "proxy_mode": "sticky"})
    assert created.json()["proxy_mode"] == "sticky"
    plain = setup_client.post("/api/presets", json={"name": "Plain"}).json()
    assert plain["proxy_mode"] == "off"
    bad = setup_client.post("/api/presets", json={"name": "Bad", "proxy_mode": "always"})
    assert bad.status_code == 422
