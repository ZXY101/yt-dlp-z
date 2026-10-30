from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.conftest import TEST_PASSWORD, MakeClient


@pytest.fixture
def feeds(tmp_path: Path) -> Path:
    return tmp_path / "feeds"


@pytest.fixture
def watch_client(make_client: MakeClient, tmp_path: Path, feeds: Path) -> TestClient:
    """A set-up client whose subscriptions read feeds written by write_feed()."""
    client = make_client(youtube_feed_url=f"file://{feeds}/{{channel_id}}.xml")
    response = client.post(
        "/api/auth/setup",
        json={"password": TEST_PASSWORD, "download_dir": str(tmp_path / "downloads")},
    )
    assert response.status_code == 204
    return client
