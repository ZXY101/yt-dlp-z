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
