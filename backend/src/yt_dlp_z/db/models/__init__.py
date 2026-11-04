"""Importing this package registers every model on Base.metadata."""

from yt_dlp_z.db.models import (
    api_token,
    cookie_file,
    job,
    preset,
    proxy,
    setting,
    subscription,
    video,
)

__all__ = ["api_token", "cookie_file", "job", "preset", "proxy", "setting", "subscription", "video"]
