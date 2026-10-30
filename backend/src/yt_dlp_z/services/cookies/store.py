"""Cookies files on disk: <config>/cookies/<id>.txt, readable only by the app's user."""

import contextlib
import os
import shutil
from collections.abc import Iterator
from pathlib import Path

PRIVATE_FILE_MODE = 0o600
PRIVATE_DIR_MODE = 0o700


def cookies_dir(config_dir: Path) -> Path:
    return config_dir / "cookies"


def cookie_path(config_dir: Path, cookie_id: int) -> Path:
    return cookies_dir(config_dir) / f"{cookie_id}.txt"


def _private_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(PRIVATE_DIR_MODE)
    return path


def write_cookie_file(config_dir: Path, cookie_id: int, content: str) -> None:
    _private_dir(cookies_dir(config_dir))
    path = cookie_path(config_dir, cookie_id)
    # Created with private permissions from the start, never world-readable.
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, PRIVATE_FILE_MODE)
    with os.fdopen(descriptor, "w", encoding="utf-8") as file:
        file.write(content)


def delete_cookie_file(config_dir: Path, cookie_id: int) -> None:
    cookie_path(config_dir, cookie_id).unlink(missing_ok=True)


@contextlib.contextmanager
def working_copy(config_dir: Path, cookie_id: int, owner: str) -> Iterator[Path]:
    """A private copy of a cookies file for one yt-dlp run.

    yt-dlp writes cookies back to the file when it exits. A copy per run keeps
    concurrent downloads from overwriting each other's changes to the same file.
    """
    source = cookie_path(config_dir, cookie_id)
    if not source.exists():
        raise FileNotFoundError(source)
    copy = _private_dir(cookies_dir(config_dir) / "running") / f"{owner}.txt"
    shutil.copyfile(source, copy)
    copy.chmod(PRIVATE_FILE_MODE)
    try:
        yield copy
    finally:
        copy.unlink(missing_ok=True)
