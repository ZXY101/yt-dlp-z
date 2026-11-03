from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import MakeClient


def test_health(client: TestClient) -> None:
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["version"]


def test_spa_serves_assets_and_falls_back_to_index(client: TestClient) -> None:
    assert client.get("/assets/app.js").text == "console.log('app')"
    assert client.get("/").text == "<html>app</html>"
    assert client.get("/settings/deep/link").text == "<html>app</html>"


def test_spa_blocks_traversal(client: TestClient, tmp_path: Path) -> None:
    (tmp_path / "secret.txt").write_text("secret")
    response = client.get("/..%2Fsecret.txt")
    assert "secret" not in response.text


def test_unknown_api_route_is_404(client: TestClient) -> None:
    assert client.get("/api/nope").status_code == 404


def test_missing_frontend_build_explains_itself(make_client: MakeClient, tmp_path: Path) -> None:
    client = make_client(frontend_dist=tmp_path / "missing")
    response = client.get("/")
    assert response.status_code == 404
    assert "npm run build" in response.json()["detail"]


def test_reset_endpoint_only_in_test_mode(make_client: MakeClient, tmp_path: Path) -> None:
    client = make_client()
    client.post("/api/auth/setup", json={"download_dir": str(tmp_path), "password": "x" * 10})
    assert client.post("/api/test/reset").status_code == 204
    assert client.get("/api/auth/status").json()["setup_required"] is True

    production = make_client(test_mode=False, config_dir=tmp_path / "prod")
    assert production.post("/api/test/reset").status_code in {404, 405}


def test_index_is_revalidated_and_hashed_assets_are_cached(client: TestClient) -> None:
    """Regression: phones kept showing the previous release after an update."""
    assert client.get("/").headers["cache-control"] == "no-cache"
    assert client.get("/settings").headers["cache-control"] == "no-cache"
    assert "immutable" in client.get("/assets/app.js").headers["cache-control"]
