from pathlib import Path

import pytest

from yt_dlp_z.services.paths import InvalidPathError, prepare_download_dir


def test_creates_missing_folder(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b"
    assert prepare_download_dir(str(target)) == target.resolve()
    assert target.is_dir()


def test_rejects_relative_paths() -> None:
    with pytest.raises(InvalidPathError, match="absolute"):
        prepare_download_dir("relative/folder")


def test_rejects_path_blocked_by_a_file(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("")
    with pytest.raises(InvalidPathError, match="Cannot create"):
        prepare_download_dir(str(blocker / "child"))


def test_rejects_unwritable_folder(tmp_path: Path) -> None:
    locked = tmp_path / "locked"
    locked.mkdir(mode=0o500)
    try:
        with pytest.raises(InvalidPathError, match="not writable"):
            prepare_download_dir(str(locked))
    finally:
        locked.chmod(0o700)
