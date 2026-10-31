from fastapi.testclient import TestClient

from tests.conftest import MakeClient, wait_for_job
from tests.integration.test_jobs_api import FINISHED, start
from tests.ntfy_server import fake_ntfy

ALL_EVENTS = ["recording_started", "download_finished", "download_failed", "problems"]


def test_defaults(setup_client: TestClient) -> None:
    assert setup_client.get("/api/notifications").json() == {
        "server": "https://ntfy.sh",
        "topic": "",
        "events": ALL_EVENTS,
        "has_token": False,
    }


def test_the_token_is_kept_but_never_sent_back(
    setup_client: TestClient, make_client: MakeClient
) -> None:
    body = {"server": "https://ntfy.example.com", "topic": "my-downloads", "token": "tk_secret"}
    saved = setup_client.put("/api/notifications", json={**body, "events": ["problems"]}).json()
    assert saved == {
        "server": "https://ntfy.example.com",
        "topic": "my-downloads",
        "events": ["problems"],
        "has_token": True,
    }
    assert "tk_secret" not in setup_client.get("/api/notifications").text

    kept = setup_client.put("/api/notifications", json={"topic": "other"}).json()
    assert kept["has_token"] is True
    removed = setup_client.put("/api/notifications", json={"topic": "other", "token": ""}).json()
    assert removed["has_token"] is False


def test_settings_survive_a_restart(setup_client: TestClient, make_client: MakeClient) -> None:
    setup_client.put("/api/notifications", json={"topic": "kept", "events": []})
    restarted = make_client()
    restarted.cookies = setup_client.cookies
    assert restarted.get("/api/notifications").json()["topic"] == "kept"
    assert restarted.get("/api/notifications").json()["events"] == []


def test_bad_settings_are_rejected(setup_client: TestClient) -> None:
    for body in ({"topic": "has spaces"}, {"server": "ntfy.sh"}, {"events": ["nope"]}):
        assert setup_client.put("/api/notifications", json=body).status_code == 422


def test_test_message_uses_the_unsaved_settings(setup_client: TestClient) -> None:
    with fake_ntfy() as ntfy:
        response = setup_client.post(
            "/api/notifications/test", json={"server": ntfy.url, "topic": "t", "token": "tk"}
        )
        assert response.status_code == 204
        assert ntfy.wait_for(1)[0]["message"] == "Notifications work."
        assert ntfy.auth == ["Bearer tk"]
    assert setup_client.get("/api/notifications").json()["topic"] == ""


def test_test_message_errors(setup_client: TestClient) -> None:
    assert setup_client.post("/api/notifications/test", json={}).status_code == 422
    with fake_ntfy() as ntfy:
        ntfy.status = 401
        response = setup_client.post(
            "/api/notifications/test", json={"server": ntfy.url, "topic": "t"}
        )
    assert response.status_code == 502
    assert response.json()["detail"] == "The ntfy server refused the access token."


def test_downloads_send_notifications(setup_client: TestClient) -> None:
    with fake_ntfy() as ntfy:
        setup_client.put("/api/notifications", json={"server": ntfy.url, "topic": "dl"})
        done = start(setup_client, "https://example.com/watch/abc")
        wait_for_job(setup_client, done["id"], FINISHED)
        failed = start(setup_client, "https://example.com/fail")
        wait_for_job(setup_client, failed["id"], FINISHED)
        ntfy.wait_for(2)
    assert ntfy.titles() == ["Download finished", "Download failed"]
    assert ntfy.received[0]["message"] == "Fake video abc"
    assert ntfy.received[1]["topic"] == "dl"
