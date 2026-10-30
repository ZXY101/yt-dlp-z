from pathlib import Path

import pytest

from yt_dlp_z.services.folders import suggest_folders
from yt_dlp_z.services.paths import InvalidPathError


@pytest.fixture
def base(tmp_path: Path) -> Path:
    base = tmp_path / "downloads"
    for folder in ["Music/Albums", "Music/Live", "videos", ".hidden"]:
        (base / folder).mkdir(parents=True)
    (base / "notes.txt").write_text("not a folder")
    return base


def test_lists_top_level_folders_without_files_or_hidden_ones(base: Path) -> None:
    assert suggest_folders("", base, []) == ["Music", "videos"]


def test_lists_sub_folders_as_typed(base: Path) -> None:
    assert suggest_folders("Music", base, []) == ["Music/Albums", "Music/Live"]
    assert suggest_folders("Music/", base, []) == ["Music/Albums", "Music/Live"]
    absolute = str(base / "Music")
    assert suggest_folders(absolute, base, []) == [f"{absolute}/Albums", f"{absolute}/Live"]


def test_offers_extra_roots_at_the_top(base: Path, tmp_path: Path) -> None:
    extra = tmp_path / "archive"
    extra.mkdir()
    assert suggest_folders("", base, [extra]) == ["Music", "videos", str(extra)]


def test_missing_folders_have_no_suggestions(base: Path) -> None:
    assert suggest_folders("not/yet", base, []) == []


@pytest.mark.parametrize("parent", ["..", "/etc", "Music/../../"])
def test_refuses_folders_outside_the_roots(base: Path, parent: str) -> None:
    with pytest.raises(InvalidPathError):
        suggest_folders(parent, base, [])


def test_hides_symlinks_that_leave_the_roots(base: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (base / "escape").symlink_to(outside)
    (base / "shortcut").symlink_to(base / "videos")
    assert suggest_folders("", base, []) == ["Music", "shortcut", "videos"]
