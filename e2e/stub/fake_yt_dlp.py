#!/usr/bin/env python3
"""Stand-in for yt-dlp in tests. Never touches the network.

Understands the command line yt-dlp-z builds (see backend services/ytdlp/command.py)
and prints the same marker lines real yt-dlp prints through those templates.
The URL picks the behaviour:
  ...fail...      exits with an error
  ...slow...      downloads for about a minute (for cancel tests)
  ...stubborn...  slow, and ignores SIGTERM (for the force-kill fallback)
  anything else   finishes in about a quarter of a second
With --simulate (the cookies check) it prints the title, or fails for ...fail... URLs.
With --cookies it reports how many cookie lines the file had, so tests can see it was passed.
"""

import json
import signal
import sys
import time
from pathlib import Path

PROGRESS = "[ytdlpz:progress]"
INFO = "[ytdlpz:info]"
FILE = "[ytdlpz:file]"
TOTAL_BYTES = 1_000_000


def values_of(args: list[str], flag: str) -> list[str]:
    return [args[i + 1] for i, arg in enumerate(args[:-1]) if arg == flag]


def emit(line: str) -> None:
    print(line, flush=True)


def simulate(url: str, title: str) -> int:
    if "fail" in url:
        emit("ERROR: [fake] Sign in to confirm you're not a bot")
        return 1
    emit(title)
    return 0


def report_cookies(args: list[str]) -> None:
    for path in values_of(args, "--cookies"):
        lines = Path(path).read_text().splitlines()
        cookies = [line for line in lines if line and not line.startswith("# ")]
        emit(f"[fake] cookies: {len(cookies)}")


def main() -> int:
    args = sys.argv[1:]
    url = args[args.index("--") + 1]
    video_id = url.rstrip("/").rsplit("/", 1)[-1] or "video"
    title = f"Fake video {video_id}"
    if "--simulate" in args:
        return simulate(url, title)
    emit("[fake] args: " + " ".join(args[: args.index("--")]))
    report_cookies(args)
    home = Path(next(v for v in values_of(args, "--paths") if v.startswith("home:"))[5:])

    if "fail" in url:
        emit("ERROR: [fake] This video is unavailable")
        return 1
    if "stubborn" in url:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    steps, delay = (600, 0.1) if "slow" in url or "stubborn" in url else (5, 0.05)

    emit(INFO + json.dumps({"id": video_id, "title": title, "webpage_url": url}))
    for step in range(1, steps + 1):
        downloaded = TOTAL_BYTES * step // steps
        progress = {
            "status": "downloading",
            "downloaded_bytes": downloaded,
            "total_bytes": TOTAL_BYTES,
            "speed": 250_000.0,
            "eta": steps - step,
        }
        emit(PROGRESS + json.dumps(progress))
        time.sleep(delay)

    target = home / f"{title} [{video_id}].mp4"
    target.write_bytes(b"fake video")
    emit(PROGRESS + json.dumps({"status": "finished", "downloaded_bytes": TOTAL_BYTES}))
    emit(FILE + json.dumps(str(target)))
    emit("[fake] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
