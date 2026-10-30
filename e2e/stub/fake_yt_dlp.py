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
With -J it prints metadata instead (see metadata()): a channel for /@handle URLs,
otherwise a video whose id picks its kind (short, upcoming, live, members, broken, long);
members-only videos only open with --cookies.
With --cookies it reports how many cookie lines the file had, so tests can see it was passed.
"""

import json
import signal
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

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


def fail_json(message: str) -> int:
    print(f"ERROR: [fake] {message}", file=sys.stderr, flush=True)
    return 1


def channel_metadata(url: str) -> int:
    handle = urlparse(url).path.strip("/").split("/")[0].removeprefix("@")
    if "fail" in handle:
        return fail_json("This channel does not exist")
    channel_id = f"UC{handle}"
    channel_url = f"https://www.youtube.com/channel/{channel_id}"
    data = {"id": channel_id, "channel_id": channel_id, "channel": f"Fake {handle}"}
    emit(json.dumps({**data, "channel_url": channel_url, "entries": []}))
    return 0


def video_metadata(video_id: str, has_cookies: bool) -> int:
    if "members" in video_id and not has_cookies:
        return fail_json("Join this channel to get access to members-only content like this video")
    if "broken" in video_id:
        return fail_json("This video is unavailable")
    data: dict[str, object] = {
        "id": video_id,
        "title": f"Fake video {video_id}",
        "duration": 7200 if "long" in video_id else 300,
        "live_status": "not_live",
        "media_type": "short" if "short" in video_id else "video",
        "webpage_url": f"https://www.youtube.com/watch?v={video_id}",
    }
    if "members" in video_id:
        data["availability"] = "subscriber_only"
    if "upcoming" in video_id:
        data.update(live_status="is_upcoming", duration=None, release_timestamp=4_102_444_800)
    elif "live" in video_id:
        data.update(live_status="is_live", duration=None)
    emit(json.dumps(data))
    return 0


def metadata(url: str, args: list[str]) -> int:
    if "/@" in url:
        return channel_metadata(url)
    return video_metadata(video_id_of(url), has_cookies="--cookies" in args)


def video_id_of(url: str) -> str:
    query_id = parse_qs(urlparse(url).query).get("v")
    if query_id:
        return query_id[0]
    return url.rstrip("/").rsplit("/", 1)[-1] or "video"


def report_cookies(args: list[str]) -> None:
    for path in values_of(args, "--cookies"):
        lines = Path(path).read_text().splitlines()
        cookies = [line for line in lines if line and not line.startswith("# ")]
        emit(f"[fake] cookies: {len(cookies)}")


def main() -> int:
    args = sys.argv[1:]
    url = args[args.index("--") + 1]
    if "-J" in args:
        return metadata(url, args)
    video_id = video_id_of(url)
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
