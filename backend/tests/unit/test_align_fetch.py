"""fetch_audio pipes yt-dlp into ffmpeg: which error wins, and that cancelling stops both."""

import asyncio
import os
import sys
from pathlib import Path

import pytest

from yt_dlp_z.services.align.fetch import FetchError, FetchHooks, FetchRequest, Tools, fetch_audio

# Tiny stand-ins run with `python -c`; the arguments fetch_audio adds are ignored.
FLOOD_THEN_BROKEN_PIPE = """
import sys
try:
    while True:
        sys.stdout.buffer.write(b"x" * 65536)
        sys.stdout.buffer.flush()
except BrokenPipeError:
    print("ERROR: [Errno 32] Broken pipe", file=sys.stderr, flush=True)
    sys.exit(1)
"""
UNAVAILABLE = """
import sys
print("ERROR: [youtube] abc: Video unavailable", file=sys.stderr, flush=True)
sys.exit(1)
"""
SENDS_AUDIO = "import sys; sys.stdout.buffer.write(b'audio')"
# Refused the first time (a marker file in the work folder remembers), fine the second.
REFUSED_ONCE = """
import pathlib, sys
marker = pathlib.Path("refused-once")
if not marker.exists():
    marker.write_text("x")
    print("ERROR: unable to download video data: HTTP Error 403: Forbidden", file=sys.stderr)
    sys.exit(1)
sys.stdout.buffer.write(b"audio")
"""
ALWAYS_REFUSED = """
import sys
print("ERROR: unable to download video data: HTTP Error 403: Forbidden", file=sys.stderr)
sys.exit(1)
"""
HANGS = "import time; time.sleep(600)"
FFMPEG_BAD_HEADER = """
import sys
print("pipe:0: Invalid data found when processing input", file=sys.stderr)
sys.exit(1)
"""
FFMPEG_READS_EVERYTHING = """
import sys
data = sys.stdin.buffer.read()
if not data:
    print("pipe:0: End of file", file=sys.stderr)
    sys.exit(1)
"""
FFMPEG_WRITES_NOTHING = "import sys; sys.stdin.buffer.read()"
FFMPEG_COPIES = """
import pathlib, sys
pathlib.Path(sys.argv[-1]).write_bytes(sys.stdin.buffer.read())
"""
FFMPEG_NOTES_PID_AND_HANGS = """
import os, sys, time
open(sys.argv[-1] + ".pid", "w").write(str(os.getpid()))
time.sleep(600)
"""


def tools(ytdlp: str, ffmpeg: str) -> Tools:
    return Tools(ytdlp=[sys.executable, "-c", ytdlp], ffmpeg=[sys.executable, "-c", ffmpeg])


def request(tmp_path: Path) -> FetchRequest:
    return FetchRequest("https://www.youtube.com/watch?v=abc", tmp_path, "audio-0")


async def no_progress(_progress: float) -> None:
    return None


HOOKS = FetchHooks(on_progress=no_progress, on_converting=lambda: None)


async def test_ffmpeg_stopping_first_reports_ffmpeg_not_the_broken_pipe(tmp_path: Path) -> None:
    flooding = tools(FLOOD_THEN_BROKEN_PIPE, FFMPEG_BAD_HEADER)
    with pytest.raises(FetchError, match="ffmpeg couldn't read the audio: pipe:0: Invalid data"):
        await fetch_audio(flooding, request(tmp_path), HOOKS)


async def test_a_ytdlp_error_wins_over_ffmpeg_seeing_no_input(tmp_path: Path) -> None:
    with pytest.raises(FetchError, match="Video unavailable"):
        await fetch_audio(tools(UNAVAILABLE, FFMPEG_READS_EVERYTHING), request(tmp_path), HOOKS)


async def test_no_audio_out_of_ffmpeg_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(FetchError, match="didn't send any audio"):
        await fetch_audio(tools(SENDS_AUDIO, FFMPEG_WRITES_NOTHING), request(tmp_path), HOOKS)


async def test_a_refused_link_is_tried_once_more(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    path = await fetch_audio(tools(REFUSED_ONCE, FFMPEG_COPIES), request(tmp_path), HOOKS)
    assert path.read_bytes() == b"audio"


async def test_a_link_refused_twice_fails(tmp_path: Path) -> None:
    with pytest.raises(FetchError, match="HTTP Error 403"):
        await fetch_audio(tools(ALWAYS_REFUSED, FFMPEG_COPIES), request(tmp_path), HOOKS)


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


async def test_cancelling_stops_ffmpeg_too(tmp_path: Path) -> None:
    task = asyncio.create_task(
        fetch_audio(tools(HANGS, FFMPEG_NOTES_PID_AND_HANGS), request(tmp_path), HOOKS)
    )
    pid_file = tmp_path / "audio-0.pcm.pid"
    for _ in range(100):
        if pid_file.exists() and pid_file.read_text():
            break
        await asyncio.sleep(0.05)
    pid = int(pid_file.read_text())
    assert alive(pid)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not alive(pid)
