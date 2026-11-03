from datetime import UTC, datetime, timedelta
from pathlib import Path

from yt_dlp_z.db.models.job import Job
from yt_dlp_z.schemas.recording import DEFAULT_RECORDING, RecordingSettings
from yt_dlp_z.services.live.plan import RecordingPlan, plan_recording
from yt_dlp_z.services.live.recorder import (
    number_first_part,
    part_args,
    part_length,
    part_template,
)

NOW = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)


def test_streams_live_for_long_are_recorded_from_now() -> None:
    fresh = plan_recording(DEFAULT_RECORDING, NOW - timedelta(hours=5), NOW)
    assert fresh == RecordingPlan(record_from_start=True, part_seconds=6 * 3600, max_seconds=None)
    # SQLite hands back naive datetimes; they are UTC.
    old = (NOW - timedelta(hours=7)).replace(tzinfo=None)
    assert not plan_recording(DEFAULT_RECORDING, old, NOW).record_from_start
    assert plan_recording(DEFAULT_RECORDING, None, NOW).record_from_start


def test_long_streams_can_be_recorded_from_the_start_up_to_the_limit() -> None:
    first_hours = DEFAULT_RECORDING.model_copy(update={"long_streams": "first_hours"})
    old = NOW - timedelta(hours=20)
    assert plan_recording(first_hours, old, NOW) == RecordingPlan(
        record_from_start=True, part_seconds=6 * 3600, max_seconds=6 * 3600
    )
    # A shorter maximum still wins; streams under the limit are recorded whole.
    shorter = first_hours.model_copy(update={"max_hours": 2})
    assert plan_recording(shorter, old, NOW).max_seconds == 2 * 3600
    assert plan_recording(first_hours, NOW - timedelta(hours=5), NOW).max_seconds is None


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
    # The first part keeps the plain name until a second part starts.
    assert part_args(split, 1) == ["--wait-for-video", "30-300"]
    assert part_args(split, 2)[-2:] == ["--output", "%(title)s (part 2).%(ext)s"]


def test_part_length_respects_the_maximum() -> None:
    assert part_length(Job(part_seconds=None, max_seconds=None), 0) is None
    assert part_length(Job(part_seconds=60, max_seconds=None), 500) == 60
    assert part_length(Job(part_seconds=60, max_seconds=100), 70) == 30
    assert part_length(Job(part_seconds=None, max_seconds=100), 130) == 0


def test_number_first_part(tmp_path: Path) -> None:
    video = tmp_path / "Stream [id].mkv"
    video.write_bytes(b"video")
    (tmp_path / "Stream [id].nfo").write_text("nfo")
    (tmp_path / "Stream [id] (part 2).mkv").write_bytes(b"other part")
    renamed = number_first_part(str(video))
    assert renamed == str(tmp_path / "Stream [id] (part 1).mkv")
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "Stream [id] (part 1).mkv",
        "Stream [id] (part 1).nfo",
        "Stream [id] (part 2).mkv",
    ]
    # Already numbered (an older version numbered every split part), or gone: left alone.
    assert number_first_part(renamed) == renamed
    assert number_first_part(str(tmp_path / "gone.mkv")) == str(tmp_path / "gone.mkv")
