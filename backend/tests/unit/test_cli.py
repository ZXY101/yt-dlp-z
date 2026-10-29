import os
from pathlib import Path
from typing import Any

import pytest

from yt_dlp_z import cli
from yt_dlp_z.core.config import get_settings


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for name in ("YTDLPZ_HOST", "YTDLPZ_PORT", "YTDLPZ_CONFIG_DIR"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("YTDLPZ_CONFIG_DIR", str(tmp_path / "config"))
    get_settings.cache_clear()


def test_flags_override_env(monkeypatch: pytest.MonkeyPatch) -> None:
    args = cli.build_parser().parse_args(["--host", "0.0.0.0", "--port", "9000"])  # noqa: S104
    cli.apply_overrides(args)
    assert os.environ["YTDLPZ_HOST"] == "0.0.0.0"  # noqa: S104
    assert os.environ["YTDLPZ_PORT"] == "9000"


def test_main_starts_uvicorn(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr("yt_dlp_z.cli.uvicorn.run", lambda *_, **kwargs: calls.append(kwargs))
    monkeypatch.setattr("sys.argv", ["yt-dlp-z", "--port", "9100"])
    cli.main()
    assert calls[0]["port"] == 9100
    assert calls[0]["factory"] is True


def test_reset_password_command(monkeypatch: pytest.MonkeyPatch) -> None:
    entered = iter(["new-password-1", "new-password-1"])
    monkeypatch.setattr("yt_dlp_z.cli.getpass.getpass", lambda _prompt: next(entered))
    monkeypatch.setattr("sys.argv", ["yt-dlp-z", "reset-password"])
    cli.main()
    assert get_settings().database_path.exists()


@pytest.mark.parametrize(
    ("entries", "message"),
    [(["short"], "at least"), (["long-enough-1", "different-2"], "do not match")],
)
def test_prompt_password_validates(
    monkeypatch: pytest.MonkeyPatch, entries: list[str], message: str
) -> None:
    entered = iter(entries)
    monkeypatch.setattr("yt_dlp_z.cli.getpass.getpass", lambda _prompt: next(entered))
    with pytest.raises(SystemExit, match=message):
        cli.prompt_password()
