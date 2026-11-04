"""Whether a VOD can replace its recording (services/live/vod_check.py)."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from yt_dlp_z.db.models.job import Job
from yt_dlp_z.services.live import vod_check
from yt_dlp_z.services.live.vod_check import media_seconds, reason_to_keep

FINISHED = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)
HOUR = 3600.0


def jobs(
    monkeypatch: pytest.MonkeyPatch,
    lengths: dict[str, float | None],
    ran_for: float | None = None,
) -> tuple[Job, Job]:
    async def fake_seconds(path: Path) -> float | None:
        return lengths[path.name]

    monkeypatch.setattr(vod_check, "media_seconds", fake_seconds)
    recorded = [name for name in lengths if name.startswith("part")]
    recording = Job(files=recorded, finished_at=FINISHED)
    if ran_for is not None:
        recording.stream_started = (FINISHED - timedelta(seconds=ran_for)).timestamp()
    return recording, Job(files=["vod"])


async def test_the_same_length_replaces(monkeypatch: pytest.MonkeyPatch) -> None:
    recording, vod = jobs(monkeypatch, {"part1": HOUR, "vod": HOUR - 20})
    assert await reason_to_keep(recording, vod) is None


async def test_a_longer_vod_replaces_a_recording_that_started_late(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recording, vod = jobs(monkeypatch, {"part1": HOUR, "vod": 2 * HOUR}, ran_for=2 * HOUR)
    assert await reason_to_keep(recording, vod) is None


async def test_parts_are_added_up(monkeypatch: pytest.MonkeyPatch) -> None:
    recording, vod = jobs(monkeypatch, {"part1": HOUR, "part2": HOUR, "vod": HOUR})
    reason = await reason_to_keep(recording, vod)
    assert reason is not None
    assert "60 min shorter" in reason


async def test_a_small_cut_is_noticed(monkeypatch: pytest.MonkeyPatch) -> None:
    recording, vod = jobs(monkeypatch, {"part1": HOUR, "vod": HOUR - 120})
    reason = await reason_to_keep(recording, vod)
    assert reason is not None
    assert "2 min shorter" in reason


async def test_a_cut_outside_a_late_recording_is_noticed(monkeypatch: pytest.MonkeyPatch) -> None:
    recording, vod = jobs(monkeypatch, {"part1": HOUR, "vod": 2 * HOUR}, ran_for=3 * HOUR)
    reason = await reason_to_keep(recording, vod)
    assert reason is not None
    assert "shorter than the stream ran" in reason


async def test_time_spent_merging_is_not_taken_for_a_cut(monkeypatch: pytest.MonkeyPatch) -> None:
    recording, vod = jobs(monkeypatch, {"part1": HOUR, "vod": HOUR}, ran_for=HOUR + 240)
    assert await reason_to_keep(recording, vod) is None


@pytest.mark.parametrize(
    "lengths",
    [
        {"part1": None, "vod": HOUR},
        {"part1": HOUR, "vod": None},
        {"part1": HOUR, "part2": None, "vod": HOUR},
    ],
)
async def test_what_cannot_be_measured_keeps_the_recording(
    monkeypatch: pytest.MonkeyPatch, lengths: dict[str, float | None]
) -> None:
    recording, vod = jobs(monkeypatch, lengths)
    reason = await reason_to_keep(recording, vod)
    assert reason is not None
    assert "couldn't compare" in reason


async def test_a_recording_with_no_files_is_kept(monkeypatch: pytest.MonkeyPatch) -> None:
    recording, vod = jobs(monkeypatch, {"vod": HOUR})
    assert await reason_to_keep(recording, vod) is not None


async def test_a_file_that_is_not_media_has_no_length(tmp_path: Path) -> None:
    path = tmp_path / "not media.mp4"
    path.write_bytes(b"fake video")
    assert await media_seconds(path) is None


async def test_no_ffprobe_means_no_length(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))
    assert await media_seconds(tmp_path / "video.mp4") is None
