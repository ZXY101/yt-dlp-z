"""The bgutil yt-dlp plugin, which fetches PO tokens from the server for yt-dlp.

It is pip-installed into <config>/plugins/bgutil, not next to the app: yt-dlp only loads
it when given --plugin-dirs (see plugin_args). Installed anywhere on sys.path it would load
on every run and warn about an unreachable server whenever no provider is set up. Its
version must match the server's, so it is installed for the server it will talk to.
"""

import asyncio
import shutil
from importlib import metadata
from pathlib import Path

from yt_dlp_z.services.ytdlp.pip import PIP_OPTIONS, last_line, run_pip, staging_dir, swap_in
from yt_dlp_z.services.ytdlp.pot.server import PotError

PACKAGE = "bgutil-ytdlp-pot-provider"
FOLDER = "bgutil"
TIMEOUT_SECONDS = 300


def plugin_version(plugins_dir: Path) -> str | None:
    for dist_info in (plugins_dir / FOLDER).glob("bgutil_ytdlp_pot_provider-*.dist-info"):
        return metadata.PathDistribution(dist_info).version
    return None


def plugin_args(plugins_dir: Path, url: str) -> list[str]:
    # yt-dlp looks for yt_dlp_plugins one folder below each --plugin-dirs folder.
    return [
        "--plugin-dirs",
        str(plugins_dir),
        "--extractor-args",
        f"youtubepot-bgutilhttp:base_url={url}",
    ]


def install_command(pip_command: list[str], target: Path, version: str) -> list[str]:
    # The plugin needs nothing but yt-dlp, which the app already has.
    options = [*PIP_OPTIONS, "--no-deps", "--target", str(target)]
    return [*pip_command, "install", *options, f"{PACKAGE}=={version}"]


async def install_plugin(pip_command: list[str], plugins_dir: Path, version: str) -> None:
    target = plugins_dir / FOLDER
    staging = staging_dir(target)
    try:
        async with asyncio.timeout(TIMEOUT_SECONDS):
            returncode, output = await run_pip(install_command(pip_command, staging, version))
        if returncode != 0:
            raise PotError(f"Couldn't install the PO token plugin {version}: {last_line(output)}")
        swap_in(staging, target)
    except TimeoutError as error:
        raise PotError("Installing the PO token plugin timed out.") from error
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def remove_plugin(plugins_dir: Path) -> None:
    shutil.rmtree(plugins_dir / FOLDER, ignore_errors=True)
