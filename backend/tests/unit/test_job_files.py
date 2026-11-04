from pathlib import Path

from yt_dlp_z.db.models.job import Job
from yt_dlp_z.services.jobs.files import delete_job_files, disk_usage, job_files


def make_job(folder: Path, files: list[Path], filepath: Path | None = None) -> Job:
    return Job(
        output_dir=str(folder),
        files=[str(file) for file in files],
        filepath=str(filepath) if filepath else None,
    )


def touch(folder: Path, *names: str) -> list[Path]:
    paths = [folder / name for name in names]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"12345")
    return paths


def test_finds_the_files_saved_beside_each_media_file(tmp_path: Path) -> None:
    video, *_ = touch(
        tmp_path,
        "Clip [a1].mp4",
        "Clip [a1].nfo",
        "Clip [a1].jpg",
        "Clip [a1].ja.srt",
        "Clip [a1].f303.mp4.part",
    )
    touch(tmp_path, "Clip [a1] extra.mp4", "Clip [a1]x.mp4", "Other [b2].mp4")
    names = [path.name for path in job_files(make_job(tmp_path, [video]))]
    assert names == [
        "Clip [a1].f303.mp4.part",
        "Clip [a1].ja.srt",
        "Clip [a1].jpg",
        "Clip [a1].mp4",
        "Clip [a1].nfo",
    ]


def test_a_short_name_does_not_claim_other_videos(tmp_path: Path) -> None:
    video, *_ = touch(tmp_path, "a.mp4", "a.nfo")
    touch(tmp_path, "a.b [x].mp4", "a b.mp4")
    assert [path.name for path in job_files(make_job(tmp_path, [video]))] == ["a.mp4", "a.nfo"]


def test_every_recording_part_belongs_to_the_job(tmp_path: Path) -> None:
    """Older jobs only know their last part."""
    *_, last = touch(
        tmp_path,
        "Stream [s1] (part 1).mp4",
        "Stream [s1] (part 1).nfo",
        "Stream [s1] (part 2).mp4",
    )
    found = [path.name for path in job_files(make_job(tmp_path, [], filepath=last))]
    assert found == [
        "Stream [s1] (part 1).mp4",
        "Stream [s1] (part 1).nfo",
        "Stream [s1] (part 2).mp4",
    ]


def test_files_outside_the_download_folder_are_never_touched(tmp_path: Path) -> None:
    folder = tmp_path / "downloads"
    folder.mkdir()
    (outside,) = touch(tmp_path, "Clip [a1].mp4")
    job = make_job(folder, [outside])
    assert job_files(job) == []
    assert delete_job_files(job) == 0
    assert outside.exists()


def test_deleting_removes_files_and_empty_season_folders(tmp_path: Path) -> None:
    season = tmp_path / "Channel" / "Season 2026"
    video, _ = touch(season, "Ep [a1].mp4", "Ep [a1].nfo")
    touch(tmp_path / "Channel", "tvshow.nfo")
    job = make_job(tmp_path, [video])
    assert disk_usage([job]).files == 2
    assert disk_usage([job]).bytes == 10
    assert delete_job_files(job) == 2
    assert not (tmp_path / "Channel").exists()


def test_the_last_video_takes_the_channel_files_with_it(tmp_path: Path) -> None:
    channel = tmp_path / "Channel"
    video, _ = touch(channel, "Ep [a1].mp4", "Ep [a1].nfo")
    touch(channel, "tvshow.nfo", "poster.jpg", "fanart.jpg", "banner.jpg")
    assert delete_job_files(make_job(tmp_path, [video])) == 2
    assert not channel.exists()
    assert tmp_path.exists()


def test_channel_files_stay_while_anything_else_is_in_the_folder(tmp_path: Path) -> None:
    channel = tmp_path / "Channel"
    video, _ = touch(channel, "Ep [a1].mp4", "Ep [a1].nfo")
    show = touch(channel, "tvshow.nfo", "poster.jpg")
    other = touch(channel, "Ep [b2].mp4")
    delete_job_files(make_job(tmp_path, [video]))
    assert all(path.exists() for path in [*show, *other])


def test_another_season_keeps_the_channel_files(tmp_path: Path) -> None:
    channel = tmp_path / "Channel"
    (video,) = touch(channel / "Season 2026", "Ep [a1].mp4")
    touch(channel / "Season 2025", "Ep [b2].mp4")
    show = touch(channel, "tvshow.nfo")
    delete_job_files(make_job(tmp_path, [video]))
    assert not (channel / "Season 2026").exists()
    assert show[0].exists()


def test_artwork_without_a_tvshow_nfo_is_not_a_channel_folder(tmp_path: Path) -> None:
    folder = tmp_path / "Mine"
    video, picture = touch(folder, "Ep [a1].mp4", "poster.jpg")
    delete_job_files(make_job(tmp_path, [video]))
    assert picture.exists()


def test_the_download_folder_itself_is_left_alone(tmp_path: Path) -> None:
    video, show = touch(tmp_path, "Ep [a1].mp4", "tvshow.nfo")
    delete_job_files(make_job(tmp_path, [video]))
    assert not video.exists()
    assert show.exists()
