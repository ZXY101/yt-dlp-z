from pathlib import Path

from yt_dlp_z.services.cookies.check import check_command
from yt_dlp_z.services.ytdlp.command import build_command
from yt_dlp_z.services.ytdlp.global_args import set_global_args
from yt_dlp_z.services.ytdlp.pot.plugin import install_command, plugin_args, plugin_version


def test_the_plugin_is_installed_on_its_own_at_the_server_version(tmp_path: Path) -> None:
    command = install_command(["pip"], tmp_path / "bgutil", "2.0.2")
    assert command[:2] == ["pip", "install"]
    assert "--no-deps" in command
    assert command[-1] == "bgutil-ytdlp-pot-provider==2.0.2"
    assert command[command.index("--target") + 1] == str(tmp_path / "bgutil")


def test_yt_dlp_loads_the_plugin_folder_and_is_told_the_server(tmp_path: Path) -> None:
    assert plugin_args(tmp_path, "http://pot:4416") == [
        "--plugin-dirs",
        str(tmp_path),
        "--extractor-args",
        "youtubepot-bgutilhttp:base_url=http://pot:4416",
    ]


def test_no_plugin_installed(tmp_path: Path) -> None:
    assert plugin_version(tmp_path) is None


def test_every_yt_dlp_command_gets_the_global_args(tmp_path: Path) -> None:
    set_global_args(["--plugin-dirs", "/plugins"])
    download = build_command(["yt-dlp"], ["--format", "best"], "https://example.com/v", tmp_path)
    # Before the user's own options, so theirs win where they overlap.
    assert download.index("/plugins") < download.index("--format")
    cookies = check_command(["yt-dlp"], tmp_path / "cookies.txt", "https://example.com/v")
    assert cookies[cookies.index("--plugin-dirs") + 1] == "/plugins"
