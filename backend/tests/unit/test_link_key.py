import pytest

from yt_dlp_z.services.jobs.link_key import job_link_key, link_key

VIDEO = "youtube:video:abc"


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=abc",
        "https://m.youtube.com/watch?v=abc&t=30s&si=share",
        "https://youtu.be/abc?si=share",
        "https://www.youtube.com/shorts/abc",
        "https://www.youtube.com/live/abc?feature=share",
        "https://music.youtube.com/watch?v=abc",
        "https://www.youtube.com/watch?v=abc&list=PL1",
    ],
)
def test_ways_of_writing_one_video_share_a_key(url: str) -> None:
    assert link_key(url) == VIDEO


def test_a_video_opened_from_a_playlist_can_mean_the_playlist() -> None:
    url = "https://www.youtube.com/watch?v=abc&list=PL1"
    assert link_key(url, whole_playlist=True) == "youtube:list:PL1"
    assert link_key("https://www.youtube.com/playlist?list=PL1") == "youtube:list:PL1"


def test_channel_pages_compare_by_path() -> None:
    assert link_key("https://www.youtube.com/@Some/") == link_key("https://youtube.com/@some")


def test_other_sites_drop_tracking_parameters_only() -> None:
    plain = link_key("https://example.org/video/1?id=5")
    assert link_key("https://www.example.org/video/1/?utm_source=x&id=5&fbclid=y") == plain
    assert link_key("https://example.org/video/1?id=6") != plain


def test_a_job_downloads_the_playlist_unless_told_not_to() -> None:
    url = "https://www.youtube.com/watch?v=abc&list=PL1"
    assert job_link_key(url, {"--no-playlist": True}) == VIDEO
    assert job_link_key(url, {"--yes-playlist": True}) == "youtube:list:PL1"
    assert job_link_key(url, {}) == "youtube:list:PL1"
