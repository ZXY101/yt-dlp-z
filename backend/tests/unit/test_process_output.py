import asyncio
from pathlib import Path

from yt_dlp_z.services.jobs.process import ProcessHooks, run_ytdlp
from yt_dlp_z.services.ytdlp.output import ProgressUpdate, Update


def test_carriage_returns_end_lines_too(tmp_path: Path) -> None:
    """Regression: ffmpeg separates progress updates with \\r, which were glued into one
    line until the next newline, so they were never parsed."""
    script = (
        "import sys, time\n"
        "sys.stdout.write('size=  1KiB time=00:00:01.00 bitrate= 8.0kbits/s\\r')\n"
        "sys.stdout.flush(); time.sleep(0.2)\n"
        "sys.stdout.write('size=  2KiB time=00:00:02.00 bitrate= 8.0kbits/s\\rdone\\n')\n"
    )
    updates: list[Update] = []

    async def on_update(update: Update) -> None:
        updates.append(update)

    command = ["python3", "-c", script]
    hooks = ProcessHooks(on_update, lambda _process: None)
    result = asyncio.run(run_ytdlp(command, tmp_path / "job.log", hooks))
    assert result.returncode == 0
    sizes = [update.downloaded_bytes for update in updates if isinstance(update, ProgressUpdate)]
    assert sizes == [1024, 2048]
    assert (tmp_path / "job.log").read_text() == "done\n"
