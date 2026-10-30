from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


def create(client: TestClient, **body: Any) -> dict[str, Any]:
    response = client.post("/api/presets", json={"name": "Music", **body})
    assert response.status_code == 201, response.text
    preset: dict[str, Any] = response.json()
    return preset


def test_create_list_update_and_delete(setup_client: TestClient) -> None:
    preset = create(
        setup_client,
        options={"--extract-audio": True, "--audio-format": "mp3"},
        extra_args="--limit-rate 2M",
        output_dir=" music ",
    )
    assert preset["output_dir"] == "music"
    assert preset["is_default"] is False

    listed = setup_client.get("/api/presets").json()
    assert [item["name"] for item in listed] == ["Music"]

    updated = setup_client.put(
        f"/api/presets/{preset['id']}", json={"name": "Podcasts", "output_dir": ""}
    ).json()
    assert updated["name"] == "Podcasts"
    assert updated["options"] == {}
    assert updated["output_dir"] is None
    assert setup_client.get(f"/api/presets/{preset['id']}").json()["name"] == "Podcasts"

    assert setup_client.delete(f"/api/presets/{preset['id']}").status_code == 204
    assert setup_client.get(f"/api/presets/{preset['id']}").status_code == 404
    assert setup_client.delete(f"/api/presets/{preset['id']}").status_code == 404


def test_only_one_preset_is_the_default(setup_client: TestClient) -> None:
    first = create(setup_client, name="First", is_default=True)
    second = create(setup_client, name="Second", is_default=True)
    defaults = {
        item["name"]: item["is_default"] for item in setup_client.get("/api/presets").json()
    }
    assert defaults == {"First": False, "Second": True}

    setup_client.put(f"/api/presets/{first['id']}", json={"name": "First", "is_default": True})
    defaults = {
        item["name"]: item["is_default"] for item in setup_client.get("/api/presets").json()
    }
    assert defaults == {"First": True, "Second": False}
    assert second["id"] != first["id"]


def test_names_are_unique(setup_client: TestClient) -> None:
    create(setup_client, name="Music")
    response = setup_client.post("/api/presets", json={"name": " Music "})
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]
    other = create(setup_client, name="Other")
    response = setup_client.put(f"/api/presets/{other['id']}", json={"name": "Music"})
    assert response.status_code == 409


def test_blank_names_are_rejected(setup_client: TestClient) -> None:
    assert setup_client.post("/api/presets", json={"name": "   "}).status_code == 422


def test_blocked_and_unknown_options_are_rejected(setup_client: TestClient) -> None:
    response = setup_client.post("/api/presets", json={"name": "x", "extra_args": "--exec ls"})
    assert response.status_code == 422
    assert "--exec isn't allowed" in response.json()["detail"]
    response = setup_client.post("/api/presets", json={"name": "x", "options": {"--nope": True}})
    assert response.status_code == 422


def test_output_dir_must_stay_inside_allowed_folders(
    setup_client: TestClient, tmp_path: Path
) -> None:
    response = setup_client.post("/api/presets", json={"name": "x", "output_dir": "../outside"})
    assert response.status_code == 422
    create(setup_client, name="Nested", output_dir="not/created/yet")
    assert not (tmp_path / "downloads" / "not").exists()


def test_presets_need_setup_and_auth(client: TestClient, make_client: Any) -> None:
    assert client.get("/api/presets").status_code == 401
    no_auth = make_client(auth_mode="none")
    assert no_auth.post("/api/presets", json={"name": "x"}).status_code == 409
