import xml.etree.ElementTree as ET
from pathlib import Path

from yt_dlp_z.db.models.job import Job
from yt_dlp_z.services.live.recorder import part_args
from yt_dlp_z.services.media_server.layout import (
    job_media_args,
    output_template,
)
from yt_dlp_z.services.media_server.nfo import write_nfo_files
from yt_dlp_z.services.ytdlp.command import NFO_MARKER
from yt_dlp_z.services.ytdlp.output import NfoUpdate, parse_line

INFO = {
    "id": "abc123",
    "title": "Morning <stream> & chat",
    "channel": "Vivi Ch.",
    "channel_id": "UCvivi",
    "upload_date": "20261031",
    "description": "First line\nSecond line",
    "duration": 3725,
}


def read(path: Path) -> dict[str, str | None]:
    root = ET.parse(path).getroot()  # noqa: S314  (files the test just had written)
    return {element.tag: element.text for element in root}


EPISODE_LAYOUT = {"folders": "channel", "file_name": "episode", "media_files": True}


def layout_job(**fields: object) -> Job:
    return Job(
        **{"options": {}, "folders": None, "file_name": None, "media_files": False, **fields}
    )


def test_folders_and_file_names_combine() -> None:
    channel = "%(channel,uploader|Unknown channel)s"
    assert output_template(layout_job(folders="channel", file_name="title_id")) == (
        f"{channel}/%(title).200B [%(id)s].%(ext)s"
    )
    assert output_template(layout_job(folders="season", file_name="dated")) == (
        f"{channel}/Season %(air_date>%Y|0000)s/[%(air_date|00000000)s] %(title).200B.%(ext)s"
    )
    assert output_template(layout_job(file_name="dated_id")) == (
        "[%(air_date|00000000)s] %(title).190B [%(id)s].%(ext)s"
    )


def test_a_folder_wraps_the_users_own_template() -> None:
    job = layout_job(options={"--output": "%(title)s.%(ext)s"})
    assert output_template(job) == "%(title)s.%(ext)s"
    assert job_media_args(job) == []
    job.folders = "channel"
    assert output_template(job) == "%(channel,uploader|Unknown channel)s/%(title)s.%(ext)s"
    job.options = {}
    assert output_template(job) == "%(channel,uploader|Unknown channel)s/%(title)s [%(id)s].%(ext)s"


def test_episodes_are_numbered_by_the_day_they_aired() -> None:
    # A stream's upload_date is when its waiting room was made; release_date is the stream.
    job = layout_job(**EPISODE_LAYOUT)
    assert "S%(air_date>%Y|0000)sE%(air_date>%m%d|0000)s" in (output_template(job) or "")
    args = job_media_args(job)
    assert args[:2] == ["--parse-metadata", r"%(release_date,upload_date|)s:(?P<air_date>\d{8})"]


def test_the_layout_replaces_the_users_template() -> None:
    job = layout_job(options={"--output": "%(title)s.%(ext)s"}, **EPISODE_LAYOUT)
    args = job_media_args(job)
    assert args[2:4] == ["--output", output_template(job)]
    assert "%(title)s.%(ext)s" not in args
    assert "--write-thumbnail" in args
    assert any(arg.startswith(f"after_move:{NFO_MARKER}") for arg in args)


def test_media_files_alone_keep_the_file_name() -> None:
    args = job_media_args(layout_job(media_files=True))
    assert "--output" not in args
    assert "--write-thumbnail" in args


def test_recording_parts_keep_the_layout() -> None:
    job = layout_job(record_from_start=True, part_seconds=60, folders="season", file_name="episode")
    template = part_args(job, 2)[-1]
    assert template.startswith((output_template(job) or "").removesuffix(".%(ext)s"))
    assert template.endswith(" (part 2).%(ext)s")


def test_nfo_lines_are_parsed() -> None:
    assert parse_line(NFO_MARKER + '{"id": "x"}') == NfoUpdate(info={"id": "x"})
    assert parse_line(NFO_MARKER + '"not a dict"') is None
    assert parse_line(NFO_MARKER + "{broken") is None


def test_season_layout_writes_episode_and_show_nfo(tmp_path: Path) -> None:
    video = tmp_path / "Vivi Ch." / "Season 2026" / "episode [abc123].mp4"
    video.parent.mkdir(parents=True)
    video.write_bytes(b"video")
    write_nfo_files({**INFO, "filepath": str(video)}, "season", tmp_path)

    episode = read(video.with_suffix(".nfo"))
    assert episode["title"] == "Morning <stream> & chat"
    assert episode["showtitle"] == "Vivi Ch."
    assert (episode["season"], episode["episode"]) == ("2026", "1031")
    assert episode["aired"] == "2026-10-31"
    assert episode["plot"] == "First line\nSecond line"
    assert episode["runtime"] == "62"
    assert episode["uniqueid"] == "abc123"
    show = read(tmp_path / "Vivi Ch." / "tvshow.nfo")
    assert show == {"title": "Vivi Ch.", "uniqueid": "UCvivi"}


def test_the_nfo_uses_the_air_date(tmp_path: Path) -> None:
    video = tmp_path / "Vivi Ch." / "stream [abc123].mp4"
    video.parent.mkdir(parents=True)
    video.write_bytes(b"video")
    info = {**INFO, "upload_date": "20261016", "air_date": "20261103", "filepath": str(video)}
    write_nfo_files(info, "channel", tmp_path)

    episode = read(video.with_suffix(".nfo"))
    assert (episode["season"], episode["episode"], episode["aired"]) == (
        "2026",
        "1103",
        "2026-11-03",
    )
    assert (tmp_path / "Vivi Ch." / "tvshow.nfo").exists()


def test_flat_layout_and_existing_show_nfo(tmp_path: Path) -> None:
    show_dir = tmp_path / "Uploader"
    show_dir.mkdir()
    (show_dir / "tvshow.nfo").write_text("edited by hand")
    video = show_dir / "clip.mkv"
    info = {"id": "z", "uploader": "Uploader", "upload_date": "bad", "filepath": str(video)}
    write_nfo_files(info, "channel", tmp_path)

    episode = read(show_dir / "clip.nfo")
    assert episode["showtitle"] == "Uploader"
    assert "season" not in episode
    assert "runtime" not in episode
    assert (show_dir / "tvshow.nfo").read_text() == "edited by hand"


def test_files_outside_the_download_folder_are_left_alone(tmp_path: Path) -> None:
    outside = tmp_path / "elsewhere" / "video.mp4"
    outside.parent.mkdir()
    write_nfo_files({**INFO, "filepath": str(outside)}, "channel", tmp_path / "downloads")
    write_nfo_files({**INFO}, "channel", tmp_path)
    assert list(tmp_path.rglob("*.nfo")) == []


def test_a_file_at_the_top_gets_no_show_nfo(tmp_path: Path) -> None:
    video = tmp_path / "video.mp4"
    write_nfo_files({**INFO, "filepath": str(video)}, "channel", tmp_path)
    assert (tmp_path / "video.nfo").exists()
    assert not (tmp_path / "tvshow.nfo").exists()
