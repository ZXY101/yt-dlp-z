import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest import TEST_PASSWORD, wait_for_job

MCP_HEADERS = {"Accept": "application/json, text/event-stream"}


def new_token(client: TestClient, name: str = "agent") -> str:
    response = client.post("/api/tokens", json={"name": name})
    assert response.status_code == 201
    token: str = response.json()["token"]
    return token


def rpc(client: TestClient, token: str, method: str, params: dict[str, Any]) -> Any:
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        headers={**MCP_HEADERS, "Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def call(client: TestClient, token: str, tool: str, **arguments: Any) -> Any:
    return rpc(client, token, "tools/call", {"name": tool, "arguments": arguments})["result"]


def signed_out(client: TestClient) -> str:
    """Makes a token, then drops the browser session so only the token can authenticate."""
    token = new_token(client)
    client.post("/api/auth/logout")
    client.cookies.clear()
    return token


def test_mcp_needs_a_token(setup_client: TestClient) -> None:
    response = setup_client.post("/mcp", json={}, headers=MCP_HEADERS)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_a_bad_token_is_refused(setup_client: TestClient) -> None:
    response = setup_client.post(
        "/mcp", json={}, headers={**MCP_HEADERS, "Authorization": "Bearer ytz_wrong"}
    )
    assert response.status_code == 401


@pytest.mark.parametrize("method", ["GET", "DELETE"])
def test_only_post_is_served_so_no_stream_blocks_shutdown(
    setup_client: TestClient, method: str
) -> None:
    token = new_token(setup_client)
    headers = {**MCP_HEADERS, "Authorization": f"Bearer {token}"}
    response = setup_client.request(method, "/mcp", headers=headers)
    assert response.status_code == 405
    assert response.headers["allow"] == "POST"


def test_a_token_reaches_the_rest_api(setup_client: TestClient) -> None:
    token = signed_out(setup_client)
    assert setup_client.get("/api/jobs").status_code == 401
    headers = {"Authorization": f"Bearer {token}"}
    assert setup_client.get("/api/jobs", headers=headers).status_code == 200


def test_a_token_cannot_manage_tokens(setup_client: TestClient) -> None:
    token = signed_out(setup_client)
    headers = {"Authorization": f"Bearer {token}"}
    assert setup_client.get("/api/tokens", headers=headers).status_code == 401
    created = setup_client.post("/api/tokens", json={"name": "more"}, headers=headers)
    assert created.status_code == 401


def test_the_token_is_only_shown_once(setup_client: TestClient) -> None:
    token = new_token(setup_client)
    assert token.startswith("ytz_")
    listed = setup_client.get("/api/tokens").json()
    assert [item["name"] for item in listed] == ["agent"]
    assert "token" not in listed[0]
    assert token not in str(listed)


def test_a_revoked_token_stops_working(setup_client: TestClient) -> None:
    token = new_token(setup_client)
    token_id = setup_client.get("/api/tokens").json()[0]["id"]
    assert setup_client.delete(f"/api/tokens/{token_id}").status_code == 204
    setup_client.cookies.clear()
    assert (
        setup_client.get("/api/jobs", headers={"Authorization": f"Bearer {token}"}).status_code
        == 401
    )


def test_names_must_be_unique(setup_client: TestClient) -> None:
    new_token(setup_client)
    assert setup_client.post("/api/tokens", json={"name": "agent"}).status_code == 409


def test_use_is_recorded(setup_client: TestClient) -> None:
    token = new_token(setup_client)
    assert setup_client.get("/api/tokens").json()[0]["last_used_at"] is None
    setup_client.cookies.clear()
    setup_client.get("/api/jobs", headers={"Authorization": f"Bearer {token}"})
    setup_client.post("/api/auth/login", json={"password": TEST_PASSWORD})
    assert setup_client.get("/api/tokens").json()[0]["last_used_at"] is not None


def test_lists_its_tools(setup_client: TestClient) -> None:
    token = signed_out(setup_client)
    tools = rpc(setup_client, token, "tools/list", {})["result"]["tools"]
    names = {tool["name"] for tool in tools}
    assert {"start_download", "update_settings", "add_subscription"} <= names
    remove = next(tool for tool in tools if tool["name"] == "remove_download")
    assert remove["annotations"]["destructiveHint"] is True


def test_start_download_runs_a_job(setup_client: TestClient) -> None:
    token = signed_out(setup_client)
    result = call(setup_client, token, "start_download", url="https://example.com/watch/ok")
    assert not result.get("isError"), result
    listed = call(setup_client, token, "list_downloads")
    assert not listed.get("isError"), listed
    assert "example.com/watch/ok" in listed["content"][0]["text"]


def test_tool_errors_carry_the_api_message(setup_client: TestClient) -> None:
    token = signed_out(setup_client)
    result = call(setup_client, token, "get_download", job_id=999)
    assert result["isError"] is True
    assert "not found" in result["content"][0]["text"].lower()


def test_update_settings_changes_only_what_it_names(setup_client: TestClient) -> None:
    before = setup_client.get("/api/settings").json()
    token = new_token(setup_client)
    result = call(
        setup_client,
        token,
        "update_settings",
        section="general",
        changes={"max_concurrent_downloads": 5},
    )
    assert not result.get("isError"), result
    assert setup_client.get("/api/settings").json() == {**before, "max_concurrent_downloads": 5}


def test_update_settings_refuses_unknown_fields(setup_client: TestClient) -> None:
    token = new_token(setup_client)
    result = call(
        setup_client, token, "update_settings", section="notifications", changes={"token": "x"}
    )
    assert result["isError"] is True
    assert "Unknown notifications settings: token" in result["content"][0]["text"]


def test_save_preset_creates_then_merges(setup_client: TestClient) -> None:
    token = new_token(setup_client)
    call(setup_client, token, "save_preset", name="Audio", changes={"options": {"-x": True}})
    call(setup_client, token, "save_preset", name="Audio", changes={"media_files": True})
    preset = next(p for p in setup_client.get("/api/presets").json() if p["name"] == "Audio")
    assert preset["options"] == {"-x": True}
    assert preset["media_files"] is True


@pytest.mark.parametrize("delete_files", [False, True])
def test_remove_download_only_deletes_files_when_asked(
    setup_client: TestClient, tmp_path: Path, delete_files: bool
) -> None:
    job_id = setup_client.post("/api/jobs", json={"url": "https://example.com/watch/ok"}).json()[
        "id"
    ]
    job = wait_for_job(setup_client, job_id, {"completed", "failed"})
    token = new_token(setup_client)
    result = call(setup_client, token, "remove_download", job_id=job_id, delete_files=delete_files)
    assert not result.get("isError"), result
    if job["filepath"]:
        assert Path(job["filepath"]).exists() is not delete_files


def job_from(result: dict[str, Any]) -> dict[str, Any]:
    assert not result.get("isError"), result
    job: dict[str, Any] = json.loads(result["content"][0]["text"])
    return job


def job_from_list(result: dict[str, Any]) -> list[dict[str, Any]]:
    assert not result.get("isError"), result
    items: list[dict[str, Any]] = []
    for block in result["content"]:
        parsed = json.loads(block["text"])
        items.extend(parsed if isinstance(parsed, list) else [parsed])
    return items


def test_a_playlist_needs_whole_playlist(setup_client: TestClient) -> None:
    token = new_token(setup_client)
    url = "https://www.youtube.com/playlist?list=PLtest"
    refused = call(setup_client, token, "start_download", url=url)
    assert refused["isError"] is True
    assert "whole_playlist" in refused["content"][0]["text"]
    assert setup_client.get("/api/jobs").json() == []
    assert job_from(call(setup_client, token, "start_download", url=url, whole_playlist=True))


def test_a_video_opened_from_a_playlist_downloads_alone(setup_client: TestClient) -> None:
    token = new_token(setup_client)
    url = "https://www.youtube.com/watch?v=abc&list=PLtest"
    job = job_from(call(setup_client, token, "start_download", url=url))
    saved = setup_client.get(f"/api/jobs/{job['id']}").json()
    assert saved["options"]["--no-playlist"] is True


def test_an_upcoming_stream_is_scheduled_as_a_recording(setup_client: TestClient) -> None:
    token = new_token(setup_client)
    url = "https://www.youtube.com/watch?v=upcoming1"
    job = job_from(call(setup_client, token, "start_download", url=url))
    assert job["kind"] == "live"
    assert job["status"] == "scheduled"
    assert job["scheduled_at"].startswith("2100-01-01T00:00:00")


def test_a_preset_without_recording_settings_uses_the_default_live_presets(
    setup_client: TestClient,
) -> None:
    token = new_token(setup_client)
    presets = setup_client.get("/api/presets").json()
    live = next(preset for preset in presets if preset["kind"] == "live")
    changes = {"recording": {**live["recording"], "part_hours": 2}}
    call(setup_client, token, "save_preset", name=live["name"], changes=changes)
    call(setup_client, token, "save_preset", name="Plain", changes={"kind": "any"})
    url = "https://www.youtube.com/watch?v=upcoming1"
    job = job_from(call(setup_client, token, "start_download", url=url, preset="Plain"))
    assert setup_client.get(f"/api/jobs/{job['id']}").json()["part_seconds"] == 2 * 3600


def test_the_default_preset_for_the_link_kind_is_used(setup_client: TestClient) -> None:
    token = new_token(setup_client)
    changes = {"kind": "video", "is_default": True, "options": {"--embed-subs": True}}
    call(setup_client, token, "save_preset", name="Videos", changes=changes)
    job = job_from(call(setup_client, token, "start_download", url="https://example.com/watch/ok"))
    assert job["preset"] == "Videos"
    assert setup_client.get(f"/api/jobs/{job['id']}").json()["options"] == {"--embed-subs": True}


def test_an_unknown_preset_is_refused_with_the_known_ones(setup_client: TestClient) -> None:
    token = new_token(setup_client)
    call(setup_client, token, "save_preset", name="Videos", changes={})
    result = call(
        setup_client, token, "start_download", url="https://example.com/watch/ok", preset="Nope"
    )
    assert result["isError"] is True
    assert "Presets: " in result["content"][0]["text"]
    assert "Videos" in result["content"][0]["text"]


def test_a_subscription_can_start_with_only_live_streams(watch_client: TestClient) -> None:
    token = new_token(watch_client)
    result = call(
        watch_client,
        token,
        "add_subscription",
        channel="https://www.youtube.com/@fake",
        filters={"content_types": ["stream"]},
    )
    created = job_from(result)
    saved = watch_client.get(f"/api/subscriptions/{created['id']}").json()
    assert saved["filters"]["content_types"] == ["stream"]
    videos = job_from_list(
        call(watch_client, token, "list_subscription_videos", subscription_id=created["id"])
    )
    assert isinstance(videos, list)


def test_debugging_tools_answer(setup_client: TestClient) -> None:
    token = new_token(setup_client)
    status = job_from(call(setup_client, token, "get_system_status"))
    assert "ytdlp_version" in status
    assert job_from_list(call(setup_client, token, "list_cookies")) == []


def test_the_skill_mentions_every_tool(setup_client: TestClient) -> None:
    """The skill ships with the tools, so a new tool must not leave it out of date."""
    token = new_token(setup_client)
    skill = Path(__file__).parents[3] / "skills" / "ytdlpz" / "SKILL.md"
    text = skill.read_text()
    tools = rpc(setup_client, token, "tools/list", {})["result"]["tools"]
    assert [tool["name"] for tool in tools if f"`{tool['name']}`" not in text] == []


def test_rebuild_chat_overlay_replaces_the_overlay(setup_client: TestClient) -> None:
    url = "https://www.youtube.com/watch?v=abc"
    created = setup_client.post("/api/jobs", json={"url": url, "live_chat": {"mode": "save"}})
    done = wait_for_job(setup_client, created.json()["id"], {"completed"})
    token = new_token(setup_client)

    style = {"max_on_screen": 5}
    result = call(setup_client, token, "rebuild_chat_overlay", job_id=done["id"], style=style)

    assert job_from(result)["chat_status"] == "overlay"
    assert Path(done["filepath"]).with_suffix(".ass").is_file()
    job = setup_client.get(f"/api/jobs/{done['id']}").json()
    assert job["live_chat"]["max_on_screen"] == 5
