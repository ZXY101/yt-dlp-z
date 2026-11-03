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
    assert not season.exists()
    assert (tmp_path / "Channel" / "tvshow.nfo").exists()
