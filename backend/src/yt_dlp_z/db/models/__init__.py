"""Importing this package registers every model on Base.metadata."""

from yt_dlp_z.db.models import cookie_file, job, preset, setting

__all__ = ["cookie_file", "job", "preset", "setting"]
