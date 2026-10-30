from pathlib import Path

import pytest

from yt_dlp_z.services.paths import InvalidPathError, prepare_download_dir, resolve_job_dir


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


def test_job_dir_defaults_to_the_base_folder(tmp_path: Path) -> None:
    assert resolve_job_dir(None, tmp_path, []) == tmp_path.resolve()
    assert resolve_job_dir("  ", tmp_path, []) == tmp_path.resolve()


def test_job_dir_relative_paths_are_inside_the_base_folder(tmp_path: Path) -> None:
    target = resolve_job_dir("music/albums", tmp_path, [])
    assert target == (tmp_path / "music" / "albums").resolve()
    assert target.is_dir()


def test_job_dir_absolute_paths_must_be_in_an_allowed_root(tmp_path: Path) -> None:
    base, extra = tmp_path / "base", tmp_path / "extra"
    base.mkdir()
    assert resolve_job_dir(str(base / "sub"), base, []) == (base / "sub").resolve()
    assert resolve_job_dir(str(extra / "x"), base, [extra]) == (extra / "x").resolve()
    with pytest.raises(InvalidPathError, match="must be inside"):
        resolve_job_dir(str(extra / "x"), base, [])


@pytest.mark.parametrize("requested", ["../outside", "a/../../outside", "/etc"])
def test_job_dir_cannot_escape(tmp_path: Path, requested: str) -> None:
    base = tmp_path / "base"
    base.mkdir()
    with pytest.raises(InvalidPathError, match="must be inside"):
        resolve_job_dir(requested, base, [])


def test_job_dir_symlinks_cannot_escape(tmp_path: Path) -> None:
    base, outside = tmp_path / "base", tmp_path / "outside"
    base.mkdir()
    outside.mkdir()
    (base / "link").symlink_to(outside)
    with pytest.raises(InvalidPathError, match="must be inside"):
        resolve_job_dir("link", base, [])
