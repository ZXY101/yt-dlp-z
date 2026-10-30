import asyncio
import sys
from pathlib import Path

import pytest

from tests.conftest import FAKE_PIP
from yt_dlp_z.schemas.ytdlp import YtdlpPreferences
from yt_dlp_z.services.ytdlp import update_check
from yt_dlp_z.services.ytdlp.update_check import Preferences, UpdateChecker, check_command
from yt_dlp_z.services.ytdlp.updater import UpdateError, YtdlpUpdater


def make_updater(tmp_path: Path, pip: list[str] | None = None) -> YtdlpUpdater:
    pip_command = pip or [sys.executable, str(FAKE_PIP)]
    return YtdlpUpdater(pip_command, tmp_path / "ytdlp", lambda: None)


def test_check_command_is_a_dry_run(tmp_path: Path) -> None:
    command = check_command(make_updater(tmp_path, ["pip"]), "nightly")
    assert command[:3] == ["pip", "install", "--dry-run"]
    assert command[-2:] == ["--pre", "yt-dlp"]
    assert command[command.index("--report") : command.index("--report") + 2] == ["--report", "-"]


@pytest.mark.parametrize(
    ("output", "message"),
    [
        ("not json", "unexpected format"),
        ('{"install": []}', "didn't find yt-dlp"),
    ],
)
async def test_unexpected_pip_answers_are_errors(tmp_path: Path, output: str, message: str) -> None:
    pip = [sys.executable, "-c", f"print({output!r})"]
    checker = UpdateChecker(make_updater(tmp_path, pip), _preferences(auto_update=False))
    with pytest.raises(UpdateError, match=message):
        await checker.check("stable")


def _preferences(*, auto_update: bool) -> Preferences:
    async def read() -> YtdlpPreferences:
        return YtdlpPreferences(channel="stable", auto_update=auto_update)

    return read


async def test_the_loop_checks_after_its_first_delay_and_survives_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(update_check, "CHECK_INTERVAL_SECONDS", 0.01)
    failing = [sys.executable, "-c", "import sys; sys.exit(1)"]
    checker = UpdateChecker(
        make_updater(tmp_path, failing), _preferences(auto_update=True), first_check_seconds=0
    )
    checker.start()
    await asyncio.sleep(0.5)
    await checker.stop()
    assert checker.latest_version is None
    await checker.stop()  # stopping twice is fine


async def test_stop_before_start_does_nothing(tmp_path: Path) -> None:
    await UpdateChecker(make_updater(tmp_path), _preferences(auto_update=False)).stop()
