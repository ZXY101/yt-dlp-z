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
With -J it prints metadata instead (see metadata()): a channel (its tabs) for /@handle
URLs, a playlist of 24 for ?list= URLs (unless --no-playlist), the streams tab for /channel/<id>/streams URLs (entries for ids containing "streamer",
an error for "broken"),
otherwise a video whose id picks its kind (short, upcoming, live, members, broken, long);
upcoming ones fail without --ignore-no-formats-error, as with real yt-dlp;
members-only videos only open with --cookies; "fastfail" ids refuse the link check's
fast path (player_client=android_vr), so the full check has to answer.
With --cookies it reports how many cookie lines the file had, so tests can see it was passed.
Recordings (--wait-for-video) have no total size, like a live stream, and stop cleanly on
SIGINT, saving the file. With --live-from-start progress comes as two numbered streams
("0: …" video, "1: …" audio at a tenth of the size); without it (recording from now)
ffmpeg writes the file and prints its own "size=… time=…" progress ended by \r, like
real yt-dlp. --output is honoured
for %(title)s, %(id)s and %(ext)s;
...upcoming... URLs first print yt-dlp's wait message.
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
TABS = ["Videos", "Live", "Shorts"]


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
    # Like real yt-dlp, a channel's home page lists its tabs as playlists.
    tabs = [{"_type": "playlist", "title": f"Fake {handle} - {tab}"} for tab in TABS]
    emit(json.dumps({**data, "_type": "playlist", "channel_url": channel_url, "entries": tabs}))
    return 0


def playlist_metadata(url: str) -> int:
    playlist_id = parse_qs(urlparse(url).query).get("list", ["PLfake"])[0]
    if "broken" in playlist_id:
        return fail_json("The playlist does not exist.")
    entries = [{"_type": "url", "id": f"item{n}", "title": f"Item {n}"} for n in range(1, 4)]
    data = {"_type": "playlist", "id": playlist_id, "title": f"Fake playlist {playlist_id}"}
    emit(json.dumps({**data, "playlist_count": 24, "entries": entries}))
    return 0


def video_metadata(video_id: str, args: list[str]) -> int:
    has_cookies = "--cookies" in args
    if "upcoming" in video_id and "--ignore-no-formats-error" not in args:
        # Like real yt-dlp: an upcoming stream has no formats yet.
        return fail_json("This live event will begin in 125 days.")
    if "members" in video_id and not has_cookies:
        return fail_json("Join this channel to get access to members-only content like this video")
    if "broken" in video_id:
        return fail_json("This video is unavailable")
    if "fastfail" in video_id and "player_client=android_vr" in " ".join(args):
        # The link check's fast path; real YouTube sometimes refuses that player.
        return fail_json("The page needs to be reloaded.")
    data: dict[str, object] = {
        "id": video_id,
        "title": f"Fake video {video_id}",
        "duration": 7200 if "long" in video_id else 300,
        "live_status": "not_live",
        "media_type": "short" if "short" in video_id else "video",
        "webpage_url": f"https://www.youtube.com/watch?v={video_id}",
        "uploader": "Fake channel",
        "extractor_key": "Youtube",
        "webpage_url_domain": "youtube.com",
    }
    if "members" in video_id:
        data["availability"] = "subscriber_only"
    if "upcoming" in video_id:
        data.update(live_status="is_upcoming", duration=None, release_timestamp=4_102_444_800)
    elif "live" in video_id:
        data.update(live_status="is_live", duration=None)
        if "old" in video_id:  # live for 10 hours already
            data["release_timestamp"] = int(time.time()) - 10 * 3600
    emit(json.dumps(data))
    return 0


def streams_tab(url: str) -> int:
    if "broken" in url:
        return fail_json("This channel has no streams tab")
    entries: list[dict[str, str]] = []
    if "streamer" in url:
        entries = [
            {"id": "live-tab1", "title": "Tab live"},
            {"id": "ended-tab1", "title": "Tab ended"},
            {"title": "An entry without an id"},
        ]
    emit(json.dumps({"id": "streams", "entries": entries}))
    return 0


def metadata(url: str, args: list[str]) -> int:
    if url.endswith("/streams"):
        return streams_tab(url)
    if "/@" in url:
        return channel_metadata(url)
    if "list=" in url and "--no-playlist" not in args:
        return playlist_metadata(url)
    return video_metadata(video_id_of(url), args)


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


def output_name(args: list[str], title: str, video_id: str) -> str:
    templates = values_of(args, "--output")
    template = templates[-1] if templates else "%(title)s [%(id)s].%(ext)s"
    names = {"%(title)s": title, "%(id)s": video_id, "%(ext)s": "mp4"}
    for field, value in names.items():
        template = template.replace(field, value)
    return template


class Recording:
    """Stops a recording's loop on SIGINT, like yt-dlp finishing on Ctrl+C."""

    stopped = False

    @classmethod
    def stop(cls, *_args: object) -> None:
        cls.stopped = True


def emit_progress(downloaded: int, eta: int, args: list[str]) -> None:
    live = "--wait-for-video" in args
    parallel = "--live-from-start" in args
    progress = {
        "status": "downloading",
        "downloaded_bytes": downloaded,
        "total_bytes": None if live else TOTAL_BYTES,
        "speed": 250_000.0,
        "eta": eta,
    }
    if live and not parallel:
        # ffmpeg writes recordings joined mid-stream, ending its updates with \r.
        kib = downloaded // 1024
        sys.stdout.write(f"size= {kib}KiB time=00:00:01.00 bitrate= 2000.0kbits/s\r")
        sys.stdout.flush()
    elif parallel:
        # Real recordings fetch video and audio at once, numbering each stream's lines.
        if "old" in args[-1]:
            # Catching up on a stream live for hours: yt-dlp reports fragments saved and
            # the newest fragment's number (each step saves 1% of the stream).
            step = downloaded * 600 // TOTAL_BYTES
            progress |= {"fragment_index": step * 10, "fragment_count": 1000}
        audio = {**progress, "downloaded_bytes": downloaded // 10, "progress_idx": 1}
        emit("0: " + PROGRESS + json.dumps({**progress, "progress_idx": 0}))
        emit("1: " + PROGRESS + json.dumps(audio))
    else:
        emit(PROGRESS + json.dumps(progress))


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
    live = "--wait-for-video" in args
    if live:
        signal.signal(signal.SIGINT, Recording.stop)
    if live and "upcoming" in url:
        emit("[wait] Waiting for the stream to start")

    emit(INFO + json.dumps({"id": video_id, "title": title, "webpage_url": url}))
    for step in range(1, steps + 1):
        if Recording.stopped:
            break
        emit_progress(TOTAL_BYTES * step // steps, steps - step, args)
        time.sleep(delay)

    target = home / output_name(args, title, video_id)
    target.write_bytes(b"fake video")
    emit(PROGRESS + json.dumps({"status": "finished", "downloaded_bytes": TOTAL_BYTES}))
    emit(FILE + json.dumps(str(target)))
    emit("[fake] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
