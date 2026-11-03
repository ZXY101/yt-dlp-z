"""Arguments added to every yt-dlp run: downloads, recordings, link checks, channel checks.

Set by the PO token provider (services/ytdlp/pot). Kept here, process-wide, like the
PYTHONPATH the updater sets, so the many places that start yt-dlp don't each need it
passed in.
"""

_args: list[str] = []


def global_args() -> list[str]:
    return list(_args)


def set_global_args(args: list[str]) -> None:
    _args[:] = args
