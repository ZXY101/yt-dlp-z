import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

MCP_HEADERS = {"Accept": "application/json, text/event-stream"}
VIDEO = "https://www.youtube.com/watch?v=abc"


def send_token(client: TestClient) -> dict[str, str]:
    """Makes a send-only token and drops the browser session, so only the token counts."""
    response = client.post("/api/tokens", json={"name": "extension", "scope": "send"})
    assert response.status_code == 201
    assert response.json()["scope"] == "send"
    client.cookies.clear()
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_tokens_have_full_access_unless_asked(setup_client: TestClient) -> None:
    setup_client.post("/api/tokens", json={"name": "agent"})
    assert setup_client.get("/api/tokens").json()[0]["scope"] == "full"


def test_a_send_token_can_list_presets_check_and_send(setup_client: TestClient) -> None:
    headers = send_token(setup_client)
    assert setup_client.get("/api/presets", headers=headers).status_code == 200
    probed = setup_client.post("/api/media/probe", json={"url": VIDEO}, headers=headers)
    assert probed.status_code == 200
    sent = setup_client.post("/api/jobs/send", json={"url": VIDEO}, headers=headers)
    assert sent.status_code == 201


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/jobs"),
        ("POST", "/api/jobs"),
        ("DELETE", "/api/jobs/1"),
        ("GET", "/api/presets/1"),
        ("POST", "/api/presets"),
        ("GET", "/api/settings"),
        ("GET", "/api/cookies"),
        ("GET", "/api/subscriptions"),
    ],
)
def test_a_send_token_is_refused_elsewhere(
    setup_client: TestClient, method: str, path: str
) -> None:
    headers = send_token(setup_client)
    response = setup_client.request(method, path, headers=headers, json={})
    assert response.status_code == 403
    assert response.json()["detail"] == "This token can only send links"


def test_a_send_token_cannot_manage_tokens_or_use_mcp(setup_client: TestClient) -> None:
    headers = send_token(setup_client)
    assert setup_client.get("/api/tokens", headers=headers).status_code == 401
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    mcp = setup_client.post("/mcp", json=body, headers={**MCP_HEADERS, **headers})
    assert mcp.status_code == 401


def test_a_send_token_gets_no_event_stream(setup_client: TestClient) -> None:
    headers = send_token(setup_client)
    with (
        pytest.raises(WebSocketDisconnect) as closed,
        setup_client.websocket_connect("/api/ws", headers=headers),
    ):
        pass
    assert closed.value.code == 4401


def test_a_send_token_is_not_signed_in(setup_client: TestClient) -> None:
    headers = send_token(setup_client)
    status = setup_client.get("/api/auth/status", headers=headers).json()
    assert status["authenticated"] is False
