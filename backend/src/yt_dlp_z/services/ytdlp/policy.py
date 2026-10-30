"""Which yt-dlp options a web user may pass, and checks on their values."""

import re

from yt_dlp_z.services.ytdlp.errors import ArgumentError

# yt-dlp-z sets these itself; allowing them would bypass its own settings.
MANAGED_OPTIONS = {
    "--paths": "Choose the download folder in yt-dlp-z instead.",
    "--cookies": "Cookies are managed by yt-dlp-z.",
    "--cookies-from-browser": "Cookies are managed by yt-dlp-z.",
    "--download-archive": "The download archive is managed by yt-dlp-z.",
    "--update": "Update yt-dlp from yt-dlp-z instead.",
    "--update-to": "Update yt-dlp from yt-dlp-z instead.",
    "--batch-file": "Add each URL as a download instead.",
}

# These can run programs or read/write files outside the download folder.
# YTDLPZ_ALLOW_UNSAFE_OPTIONS lifts this list (but not MANAGED_OPTIONS).
UNSAFE_OPTIONS = {
    "--exec": "It runs shell commands.",
    "--netrc-cmd": "It runs shell commands.",
    "--plugin-dirs": "It loads Python code from a folder.",
    "--ffmpeg-location": "It can run any program.",
    "--downloader": "It can run any program.",
    "--js-runtimes": "It can run any program.",
    "--postprocessor-args": "It passes raw arguments to ffmpeg, which can write anywhere.",
    "--downloader-args": "It passes raw arguments to other programs.",
    "--load-info-json": "It reads any file on the server.",
    "--netrc-location": "It reads any file on the server.",
    "--config-locations": "It reads config files from anywhere.",
    "--print-to-file": "It writes files anywhere.",
    "--cache-dir": "It writes files anywhere.",
    "--enable-file-urls": "It lets URLs read local files.",
    "--alias": "It can define aliases for blocked options.",
}

_TYPE_PREFIX = re.compile(r"^[a-z_]+:")
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")


def blocked_reason(flag: str, *, allow_unsafe: bool) -> str | None:
    if flag in MANAGED_OPTIONS:
        return MANAGED_OPTIONS[flag]
    if not allow_unsafe and flag in UNSAFE_OPTIONS:
        return f"{UNSAFE_OPTIONS[flag]} Set YTDLPZ_ALLOW_UNSAFE_OPTIONS to allow it."
    return None


def check_output_template(template: str) -> None:
    """Output templates must stay inside the download folder."""
    path = _TYPE_PREFIX.sub("", template, count=1)
    escapes = (
        path.startswith(("/", "\\", "~"))
        or _WINDOWS_DRIVE.match(path) is not None
        or ".." in re.split(r"[\\/]", path)
    )
    if escapes:
        raise ArgumentError(
            f"Output template {template!r} must be a relative path inside the download folder."
        )
