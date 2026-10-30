from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import MakeClient


def test_suggests_folders_inside_the_download_folder(
    setup_client: TestClient, tmp_path: Path
) -> None:
    (tmp_path / "downloads" / "Music").mkdir(parents=True)
    response = setup_client.get("/api/folders")
    assert response.json() == {"folders": ["Music"]}
    assert setup_client.get("/api/folders", params={"parent": "Music"}).json() == {"folders": []}
    assert setup_client.get("/api/folders", params={"parent": "/etc"}).status_code == 422


def test_folders_need_auth_and_setup(client: TestClient, make_client: MakeClient) -> None:
    assert client.get("/api/folders").status_code == 401
    assert make_client(auth_mode="none").get("/api/folders").status_code == 409
