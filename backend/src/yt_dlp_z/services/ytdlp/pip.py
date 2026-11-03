"""pip installs into a folder of their own: yt-dlp updates and the PO token plugin."""

import asyncio
import shutil
from pathlib import Path

from yt_dlp_z.services.ytdlp.communicate import communicate

PIP_OPTIONS = ["--no-input", "--disable-pip-version-check"]


async def run_pip(command: list[str]) -> tuple[int, bytes]:
    """Returns pip's exit code and output. Callers wrap it in asyncio.timeout."""
    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    output, _ = await communicate(process)
    return process.returncode or 0, output


def last_line(output: bytes) -> str:
    lines = output.decode(errors="replace").strip().splitlines()
    return lines[-1] if lines else "no output"


def staging_dir(target: Path) -> Path:
    """An empty folder next to the target. Installs go there first and are then swapped
    in, so a failed or half-done install never breaks the copy in use."""
    staging = target.with_name(f"{target.name}.new")
    shutil.rmtree(staging, ignore_errors=True)
    staging.parent.mkdir(parents=True, exist_ok=True)
    return staging


def swap_in(staging: Path, target: Path) -> None:
    old = target.with_name(f"{target.name}.old")
    shutil.rmtree(old, ignore_errors=True)
    if target.exists():
        target.rename(old)
    staging.rename(target)
    shutil.rmtree(old, ignore_errors=True)
