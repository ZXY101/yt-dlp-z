import json
from pathlib import Path

import pytest

from yt_dlp_z.services.ytdlp.command import (
    FILE_MARKER,
    INFO_MARKER,
    PROGRESS_MARKER,
    build_command,
)
from yt_dlp_z.services.ytdlp.output import (
    FileUpdate,
    InfoUpdate,
    ProgressUpdate,
    combine_parts,
    error_message,
    parse_line,
)


def progress_line(data: object) -> str:
    return PROGRESS_MARKER + json.dumps(data)


def test_progress_with_total() -> None:
    line = progress_line(
        {
            "status": "downloading",
            "downloaded_bytes": 250,
            "total_bytes": 1000,
            "speed": 10.5,
            "eta": 7,
        }
    )
    assert parse_line(line) == ProgressUpdate(250, 1000, 10.5, 7, 25.0)


def test_progress_with_estimate_and_finished() -> None:
    estimate = parse_line(progress_line({"downloaded_bytes": 50, "total_bytes_estimate": 200}))
    finished = parse_line(progress_line({"status": "finished", "downloaded_bytes": 200}))
    assert isinstance(estimate, ProgressUpdate)
    assert estimate.progress == 25.0
    assert isinstance(finished, ProgressUpdate)
    assert finished.progress == 100.0


def test_progress_without_total_has_no_percentage() -> None:
    update = parse_line(progress_line({"downloaded_bytes": 50, "speed": None}))
    assert update == ProgressUpdate(50, None, None, None, None)


def test_info_and_file_lines() -> None:
    assert parse_line(INFO_MARKER + '{"title": "A video"}') == InfoUpdate("A video")
    assert parse_line(INFO_MARKER + '{"title": null}') == InfoUpdate(None)
    assert parse_line(FILE_MARKER + '"/downloads/a.mp4"') == FileUpdate("/downloads/a.mp4")


@pytest.mark.parametrize(
    "line",
    [
        "[download] Destination: a.mp4",
        PROGRESS_MARKER + "not json",
        PROGRESS_MARKER + "[1, 2]",
        INFO_MARKER + "[]",
        FILE_MARKER + "42",
    ],
)
def test_other_lines_are_ignored(line: str) -> None:
    assert parse_line(line) is None


def test_error_message() -> None:
    assert (
        error_message("ERROR: [youtube] abc: Video unavailable")
        == "[youtube] abc: Video unavailable"
    )
    assert error_message("WARNING: something") is None


def test_command_shape(tmp_path: Path) -> None:
    command = build_command(["yt-dlp"], ["--format", "best"], "https://example.com/v", tmp_path)
    assert command[0] == "yt-dlp"
    assert "--ignore-config" in command
    assert command[-2:] == ["--", "https://example.com/v"]
    assert command[command.index("--format") + 1] == "best"
    assert f"home:{tmp_path}" in command
    templates = " ".join(command)
    assert all(marker in templates for marker in (PROGRESS_MARKER, INFO_MARKER, FILE_MARKER))


def test_parallel_progress_lines_are_numbered_per_stream() -> None:
    """Regression: live-from-start recordings download video and audio at once, and yt-dlp
    prefixes each progress line with the stream's number, which hid all progress."""
    data = {"downloaded_bytes": 300, "speed": 30.0, "progress_idx": 1, "max_progress": 2}
    update = parse_line("1: " + progress_line(data))
    assert update == ProgressUpdate(300, None, 30.0, None, None, part=1)


def test_fragment_numbers_are_read() -> None:
    data = {"downloaded_bytes": 300, "fragment_index": 12, "fragment_count": 7200}
    assert parse_line(progress_line(data)).fragments == (12, 7200)  # type: ignore[union-attr]


def test_combine_parts_adds_up_the_streams() -> None:
    video = ProgressUpdate(700, 1000, 70.0, 5, 70.0)
    audio = ProgressUpdate(100, 200, 10.0, 9, 50.0, part=1)
    assert combine_parts({0: video, 1: audio}) == ProgressUpdate(
        800, 1200, 80.0, 9, 800 / 1200 * 100
    )
    live_video = ProgressUpdate(700, None, 70.0, None, None)
    live_audio = ProgressUpdate(100, None, None, None, None, part=1)
    assert combine_parts({0: live_video, 1: live_audio}) == ProgressUpdate(
        800, None, 70.0, None, None
    )
    assert combine_parts({0: video}) == video


def test_ffmpeg_progress_counts_for_recordings_joined_mid_stream() -> None:
    """Regression: recordings from "now" are written by ffmpeg, whose progress lines were
    only logged, so the queue showed no size."""
    line = "frame=  449 fps=112 q=-1.0 size=     512KiB time=00:00:14.96 bitrate= 280.2kbits/s"
    assert parse_line(line) == ProgressUpdate(512 * 1024, None, 280.2 * 1000 / 8, None, None)
    assert parse_line("size=    2.5MiB time=00:01:00.00 bitrate=N/A speed=1x") == ProgressUpdate(
        int(2.5 * 1024 * 1024), None, None, None, None
    )
    assert parse_line("[download] size= unknown") is None
