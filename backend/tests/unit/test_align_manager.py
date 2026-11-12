import asyncio
import sys
from pathlib import Path

import pytest

from tests.conftest import FAKE_FFMPEG, FAKE_YTDLP
from yt_dlp_z.services.align import manager as manager_module
from yt_dlp_z.services.align.fetch import Tools
from yt_dlp_z.services.align.job import AlignJob, AlignState, StreamStage
from yt_dlp_z.services.align.manager import (
    IDLE_SECONDS,
    RUNNING_IDLE_SECONDS,
    AlignConfig,
    AlignManager,
)

TOOLS = Tools(ytdlp=[sys.executable, str(FAKE_YTDLP)], ffmpeg=[sys.executable, str(FAKE_FFMPEG)])
URLS = ["https://www.youtube.com/watch?v=align-60", "https://www.youtube.com/watch?v=align-30"]


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def make_manager(tmp_path: Path, clock: Clock) -> AlignManager:
    config = AlignConfig(root=tmp_path / "align", config_dir=tmp_path, tools=TOOLS, clock=clock)
    return AlignManager(config)


async def finish(job: AlignJob) -> None:
    assert job.task is not None
    await asyncio.wait_for(job.task, 30)


async def test_results_are_dropped_after_an_hour_without_a_check(tmp_path: Path) -> None:
    clock = Clock()
    manager = make_manager(tmp_path, clock)
    manager.start()
    job = manager.create(URLS, None)
    await finish(job)
    clock.now += IDLE_SECONDS - 1
    assert manager.get(job.id) is job
    clock.now += IDLE_SECONDS - 1
    await manager.sweep()
    assert manager.get(job.id) is job
    clock.now += IDLE_SECONDS + 1
    await manager.sweep()
    assert manager.get(job.id) is None
    await manager.stop()


async def test_an_abandoned_running_job_is_stopped_after_a_minute(tmp_path: Path) -> None:
    clock = Clock()
    manager = make_manager(tmp_path, clock)
    job = manager.create(["https://x.test/align-slow", URLS[1]], None)
    await asyncio.sleep(0.3)
    clock.now += RUNNING_IDLE_SECONDS - 1
    await manager.sweep()
    assert manager.get(job.id) is job
    clock.now += RUNNING_IDLE_SECONDS + 1
    await manager.sweep()
    assert manager.get(job.id) is None
    assert job.task is not None
    assert job.task.cancelled()
    await manager.stop()


async def test_each_link_reports_its_stage(tmp_path: Path) -> None:
    manager = make_manager(tmp_path, Clock())
    job = manager.create(["https://x.test/align-slow", URLS[1]], None)
    for _ in range(100):
        await asyncio.sleep(0.05)
        if job.streams[1].stage is StreamStage.READY:
            break
    slow, quick = job.streams
    assert quick.stage is StreamStage.READY
    assert slow.stage is StreamStage.DOWNLOADING
    assert 0 < slow.downloaded < 1
    assert 0.45 < job.progress < 0.9
    await manager.stop()


async def test_stop_cancels_running_jobs_and_wipes_the_audio(tmp_path: Path) -> None:
    manager = make_manager(tmp_path, Clock())
    manager.start()
    job = manager.create(["https://x.test/align-slow", URLS[1]], None)
    await asyncio.sleep(0.3)
    assert job.state is AlignState.DOWNLOADING
    assert 0 <= job.progress < 0.9
    await manager.stop()
    assert job.task is not None
    assert job.task.cancelled()
    assert not (tmp_path / "align").exists()


async def test_only_the_newest_finished_results_are_kept(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(manager_module, "MAX_KEPT", 2)
    clock = Clock()
    manager = make_manager(tmp_path, clock)
    jobs = []
    for _ in range(3):
        clock.now += 1
        job = manager.create(URLS, None)
        await finish(job)
        jobs.append(job)
    assert [manager.get(job.id) is not None for job in jobs] == [False, True, True]
    await manager.stop()


def processes_for(video_id: str) -> list[int]:
    """Running processes whose command line mentions `video_id` (Linux /proc)."""
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            command = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        if video_id.encode() in command:
            found.append(int(entry.name))
    return found


async def test_a_failing_link_stops_the_other_downloads(tmp_path: Path) -> None:
    manager = make_manager(tmp_path, Clock())
    job = manager.create(
        ["https://www.youtube.com/watch?v=align-slow-sibling", "https://x.test/fail1"], None
    )
    await finish(job)
    assert job.state is AlignState.FAILED
    assert processes_for("align-slow-sibling") == []
    await manager.stop()
