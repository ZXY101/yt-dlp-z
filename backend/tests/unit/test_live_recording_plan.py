from datetime import UTC, datetime, timedelta

from yt_dlp_z.db.models.job import Job
from yt_dlp_z.schemas.app_settings import DEFAULT_RECORDING, RecordingSettings
from yt_dlp_z.services.live.plan import RecordingPlan, plan_recording
from yt_dlp_z.services.live.recorder import part_args, part_length, part_template

NOW = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)


def test_streams_live_for_long_are_recorded_from_now() -> None:
    fresh = plan_recording(DEFAULT_RECORDING, NOW - timedelta(hours=5), NOW)
    assert fresh == RecordingPlan(record_from_start=True, part_seconds=6 * 3600, max_seconds=None)
    # SQLite hands back naive datetimes; they are UTC.
    old = (NOW - timedelta(hours=7)).replace(tzinfo=None)
    assert not plan_recording(DEFAULT_RECORDING, old, NOW).record_from_start
    assert plan_recording(DEFAULT_RECORDING, None, NOW).record_from_start


def test_turned_off_settings_mean_no_limits() -> None:
    off = RecordingSettings(part_hours=None, max_hours=2, from_start_max_hours=None)
    plan = plan_recording(off, NOW - timedelta(days=3), NOW)
    assert plan == RecordingPlan(record_from_start=True, part_seconds=None, max_seconds=7200)


def test_part_names() -> None:
    assert part_template(None, 2) == "%(title)s [%(id)s] (part 2).%(ext)s"
    assert (
        part_template("%(uploader)s/%(title)s.%(ext)s", 3)
        == "%(uploader)s/%(title)s (part 3).%(ext)s"
    )
    assert part_template("%(title)s", 4) == "%(title)s (part 4)"


def test_part_args() -> None:
    job = Job(options={}, record_from_start=True, part_seconds=None)
    assert part_args(job, 1) == ["--live-from-start", "--wait-for-video", "30-300"]
    # A continued recording (after a restart) records from now, into a numbered file.
    assert part_args(job, 2) == [
        "--wait-for-video",
        "30-300",
        "--output",
        "%(title)s [%(id)s] (part 2).%(ext)s",
    ]
    split = Job(options={"--output": "%(title)s.%(ext)s"}, record_from_start=False, part_seconds=60)
    assert part_args(split, 1)[-2:] == ["--output", "%(title)s (part 1).%(ext)s"]
    assert "--live-from-start" not in part_args(split, 1)


def test_part_length_respects_the_maximum() -> None:
    assert part_length(Job(part_seconds=None, max_seconds=None), 0) is None
    assert part_length(Job(part_seconds=60, max_seconds=None), 500) == 60
    assert part_length(Job(part_seconds=60, max_seconds=100), 70) == 30
    assert part_length(Job(part_seconds=None, max_seconds=100), 130) == 0
