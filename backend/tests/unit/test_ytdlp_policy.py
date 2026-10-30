import asyncio

import pytest

from yt_dlp_z.services.ytdlp.errors import ArgumentError
from yt_dlp_z.services.ytdlp.policy import (
    MANAGED_OPTIONS,
    UNSAFE_OPTIONS,
    blocked_reason,
    check_output_template,
)
from yt_dlp_z.services.ytdlp.schema import build_index, read_option_schema


def test_every_policy_flag_exists_in_the_installed_yt_dlp() -> None:
    """Catches yt-dlp renaming an option, which would silently unblock it."""
    index = build_index(asyncio.run(read_option_schema(allow_unsafe=False)))
    missing = [flag for flag in [*MANAGED_OPTIONS, *UNSAFE_OPTIONS] if flag not in index]
    assert missing == []
    assert all(index[flag].flag == flag for flag in [*MANAGED_OPTIONS, *UNSAFE_OPTIONS])


def test_blocked_reason() -> None:
    assert blocked_reason("--format", allow_unsafe=False) is None
    assert "YTDLPZ_ALLOW_UNSAFE_OPTIONS" in (blocked_reason("--exec", allow_unsafe=False) or "")
    assert blocked_reason("--exec", allow_unsafe=True) is None
    assert blocked_reason("--paths", allow_unsafe=True) is not None


@pytest.mark.parametrize(
    "template",
    [
        "%(title)s [%(id)s].%(ext)s",
        "%(uploader)s/%(upload_date>%Y-%m-%d)s %(title)s.%(ext)s",
        "thumbnail:%(title)s/cover.%(ext)s",
        "a..b.%(ext)s",
    ],
)
def test_output_templates_inside_the_folder_are_allowed(template: str) -> None:
    check_output_template(template)


@pytest.mark.parametrize(
    "template",
    [
        "/etc/%(title)s",
        "~/videos/%(title)s",
        "../%(title)s",
        "videos/../../%(title)s",
        "C:\\Users\\%(title)s",
        "subtitle:/tmp/%(title)s",
        "..\\%(title)s",
    ],
)
def test_output_templates_escaping_the_folder_are_rejected(template: str) -> None:
    with pytest.raises(ArgumentError):
        check_output_template(template)
