from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.integration.watch_helpers import subscribe

COOKIES = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tFAKE\tnot-a-real-value\n"


@pytest.fixture
def paused(setup_client: TestClient) -> dict[str, Any]:
    """A subscription that never polls, so these tests don't depend on a feed."""
    return subscribe(setup_client, enabled=False)


def test_list_update_and_delete(setup_client: TestClient, paused: dict[str, Any]) -> None:
    assert [item["name"] for item in setup_client.get("/api/subscriptions").json()] == ["Fake demo"]
    body = {
        "poll_minutes": 60,
        "enabled": False,
        "output_dir": " channels/demo ",
        "filters": {"content_types": ["short"], "title_include": "part \\d+"},
    }
    updated = setup_client.put(f"/api/subscriptions/{paused['id']}", json=body).json()
    assert updated["poll_minutes"] == 60
    assert updated["output_dir"] == "channels/demo"
    assert updated["filters"]["content_types"] == ["short"]
    assert updated["filters"]["title_include"] == "part \\d+"

    assert setup_client.delete(f"/api/subscriptions/{paused['id']}").status_code == 204
    assert setup_client.get(f"/api/subscriptions/{paused['id']}").status_code == 404
    assert setup_client.put(f"/api/subscriptions/{paused['id']}", json={}).status_code == 404
    assert setup_client.post(f"/api/subscriptions/{paused['id']}/check").status_code == 404
    assert setup_client.get(f"/api/subscriptions/{paused['id']}/videos").status_code == 404


def test_each_channel_is_watched_once(setup_client: TestClient, paused: dict[str, Any]) -> None:
    response = setup_client.post(
        "/api/subscriptions", json={"channel": "https://www.youtube.com/@demo/videos"}
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "You already watch Fake demo"


def test_the_channel_limit(setup_client: TestClient, paused: dict[str, Any]) -> None:
    settings = setup_client.get("/api/settings").json()
    setup_client.put("/api/settings", json={**settings, "max_subscriptions": 1})
    response = setup_client.post("/api/subscriptions", json={"channel": "@other"})
    assert response.status_code == 409
    assert "watching 1 of 1 channels" in response.json()["detail"]

    setup_client.put("/api/settings", json={**settings, "max_subscriptions": 2})
    assert setup_client.post("/api/subscriptions", json={"channel": "@other"}).status_code == 201


@pytest.mark.parametrize(
    ("channel", "message"),
    [
        ("https://example.com/@demo", "Enter a YouTube channel or playlist URL, or @handle"),
        ("@failing", "Couldn't open that channel: [fake] This channel does not exist"),
        ("https://www.youtube.com/watch?v=abc", "That address isn't a YouTube channel"),
    ],
)
def test_bad_channels_are_rejected(setup_client: TestClient, channel: str, message: str) -> None:
    response = setup_client.post("/api/subscriptions", json={"channel": channel})
    assert response.status_code == 422
    assert response.json()["detail"] == message


@pytest.mark.parametrize(
    "body",
    [
        {"filters": {"title_include": "("}},
        {"filters": {"min_duration": 60, "max_duration": 10}},
        {"filters": {"content_types": []}},
        {"poll_minutes": 1},
        {"backfill": 16},
        {"preset_id": 999},
        {"cookie_id": 999},
        {"output_dir": "/etc"},
    ],
)
def test_invalid_settings_are_rejected(setup_client: TestClient, body: dict[str, Any]) -> None:
    response = setup_client.post("/api/subscriptions", json={"channel": "@demo", **body})
    assert response.status_code == 422


def test_deleting_a_preset_or_cookies_unlinks_them(
    setup_client: TestClient, paused: dict[str, Any]
) -> None:
    preset = setup_client.post("/api/presets", json={"name": "Audio"}).json()
    cookies = setup_client.post("/api/cookies", json={"name": "Main", "content": COOKIES}).json()
    url = f"/api/subscriptions/{paused['id']}"
    body = {"preset_id": preset["id"], "cookie_id": cookies["id"], "enabled": False}
    assert setup_client.put(url, json=body).status_code == 200

    setup_client.delete(f"/api/presets/{preset['id']}")
    setup_client.delete(f"/api/cookies/{cookies['id']}")
    subscription = setup_client.get(url).json()
    assert subscription["preset_id"] is None
    assert subscription["cookie_id"] is None


def test_subscriptions_need_auth(client: TestClient) -> None:
    assert client.get("/api/subscriptions").status_code == 401
    assert client.post("/api/subscriptions", json={"channel": "@demo"}).status_code == 401
