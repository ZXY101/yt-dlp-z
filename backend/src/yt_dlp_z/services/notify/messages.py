"""What each notification says, built from a job as sent to clients."""

import re
from typing import Any

from yt_dlp_z.services.notify.ntfy import HIGH_PRIORITY, Message

# Failures in a row that suggest yt-dlp itself is broken (YouTube changed something).
FAILURE_STREAK = 3

# yt-dlp errors that mean YouTube wants a signed-in (or fresher) session.
_COOKIE_ERRORS = re.compile(
    r"sign in to confirm|cookies are no longer valid|use --cookies|login required",
    re.IGNORECASE,
)

Job = dict[str, Any]


def _name(job: Job) -> str:
    return str(job.get("title") or job["url"])


def _noun(job: Job) -> str:
    return "Recording" if job["kind"] == "live" else "Download"


def recording_started(job: Job) -> Message:
    return Message("Recording started", _name(job), ["red_circle"], click=job["url"])


def finished(job: Job) -> Message:
    return Message(f"{_noun(job)} finished", _name(job), ["white_check_mark"])


def failed(job: Job) -> Message:
    text = f"{_name(job)}\n{job.get('error') or 'Unknown error.'}"
    return Message(f"{_noun(job)} failed", text, ["x"], HIGH_PRIORITY, click=job["url"])


def needs_cookies(job: Job) -> Message | None:
    if not _COOKIE_ERRORS.search(job.get("error") or ""):
        return None
    text = (
        "YouTube asked for a sign-in. Upload fresh cookies, or check the cookies file "
        f"used by this download.\n{_name(job)}"
    )
    return Message("Cookies may have expired", text, ["warning", "cookie"], HIGH_PRIORITY)


def failure_streak() -> Message:
    text = (
        f"The last {FAILURE_STREAK} downloads all failed. yt-dlp may need an update: "
        "Settings → yt-dlp → Update now."
    )
    return Message("Downloads keep failing", text, ["warning"], HIGH_PRIORITY)


def test_message() -> Message:
    return Message("yt-dlp-z", "Notifications work.", ["tada"])
