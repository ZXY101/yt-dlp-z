"""Importing this package registers every model on Base.metadata."""

from yt_dlp_z.db.models import cookie_file, job, preset, proxy, setting, subscription, video

__all__ = ["cookie_file", "job", "preset", "proxy", "setting", "subscription", "video"]
