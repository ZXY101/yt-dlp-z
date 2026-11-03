import json
import sqlite3
from pathlib import Path

from alembic import command

from yt_dlp_z.db.migrate import alembic_config, upgrade_to_head

BEFORE_PRESET_KINDS = "52b8449b79a1"
BEFORE_JOB_FILES = "5799a7f952a0"


def test_global_recording_settings_become_a_live_stream_preset(tmp_path: Path) -> None:
    database = tmp_path / "app.db"
    command.upgrade(alembic_config(database), BEFORE_PRESET_KINDS)
    with sqlite3.connect(database) as connection:
        connection.executemany(
            "INSERT INTO settings (key, value) VALUES (?, ?)",
            [
                ("recording_part_hours", ""),
                ("recording_max_hours", "12"),
                ("recording_long_streams", "first_hours"),
                ("max_subscriptions", "8"),
            ],
        )
        connection.executemany(
            "INSERT INTO presets (name, options, extra_args, output_dir, is_default,"
            " created_at, updated_at) VALUES (?, ?, '', ?, ?, '2026-10-01', '2026-10-01')",
            [
                ("Live streams", "{}", None, False),
                ("Archive", json.dumps({"--embed-chapters": True}), "yt", True),
            ],
        )

    upgrade_to_head(database)

    with sqlite3.connect(database) as connection:
        rows = connection.execute(
            "SELECT name, kind, is_default, options, output_dir, recording FROM presets"
        ).fetchall()
        keys = [row[0] for row in connection.execute("SELECT key FROM settings")]
    live = next(row for row in rows if row[1] == "live")
    assert live[:5] == ("Live streams 2", "live", 1, '{"--embed-chapters": true}', "yt")
    assert json.loads(live[5]) == {
        "part_hours": None,
        "max_hours": 12,
        "from_start_max_hours": 6,
        "long_streams": "first_hours",
    }
    assert {row[0]: row[1] for row in rows if row[1] != "live"} == {
        "Live streams": "any",
        "Archive": "any",
    }
    assert keys == ["max_subscriptions"]


def test_jobs_get_their_known_file(tmp_path: Path) -> None:
    database = tmp_path / "app.db"
    command.upgrade(alembic_config(database), BEFORE_JOB_FILES)
    with sqlite3.connect(database) as connection:
        connection.executemany(
            "INSERT INTO jobs (url, status, options, extra_args, output_dir, filepath,"
            " created_at) VALUES ('u', 'completed', '{}', '', '/d', ?, '2026-10-01')",
            [("/d/a [x].mp4",), (None,)],
        )

    upgrade_to_head(database)

    with sqlite3.connect(database) as connection:
        rows = connection.execute("SELECT files, keep FROM jobs ORDER BY id").fetchall()
    assert [(json.loads(files), keep) for files, keep in rows] == [(["/d/a [x].mp4"], 0), ([], 0)]
