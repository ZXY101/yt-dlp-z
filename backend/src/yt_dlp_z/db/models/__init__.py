"""Importing this package registers every model on Base.metadata."""

from yt_dlp_z.db.models import job, setting

__all__ = ["job", "setting"]
