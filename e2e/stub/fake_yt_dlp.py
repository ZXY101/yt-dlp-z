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
an error for "broken"), the videos tab for /channel/<id>/videos URLs (entries for ids
containing "uploader", an error for "broken"),
otherwise a video whose id picks its kind (short, upcoming, live, members, broken, long);
upcoming ones fail without --ignore-no-formats-error, as with real yt-dlp;
members-only videos only open with --cookies; "fastfail" ids refuse the link check's
fast path (player_client=android_vr), so the full check has to answer.
With --cookies it reports how many cookie lines the file had, so tests can see it was passed.
A --proxy containing "blocked" fails downloads with YouTube's bot check, like a proxy
YouTube has flagged.
Recordings (--wait-for-video) have no total size, like a live stream, and stop cleanly on
SIGINT, saving the file. With --live-from-start progress comes as two numbered streams
("0: …" video, "1: …" audio at a tenth of the size); without it (recording from now)
ffmpeg writes the file and prints its own "size=… time=…" progress ended by \r, like
real yt-dlp. --output is honoured for any %(field)s, with fake values for the
fields media-server output uses (channel, upload_date with a >%Y or >%m%d format,
a .150B length, air_date when a --parse-metadata sets it); with --write-thumbnail it saves a .jpg next to the video; a
--print after_move:[ytdlpz:nfo] template gets the NFO fields;
--replace-in-metadata title REGEX REPLACE changes the title (and so the file name);
--write-subs --skip-download with --sub-langs live_chat fetches the chat instead of the video
and saves a sample (see save_chat): ...nochat... URLs have none, ...badchat... URLs fail,
...draggingchat... URLs take a minute. Saved as chat-N (a recording's capture) it's written as
live chat, a comment every 0.1 s until stopped, into the .part file yt-dlp keeps until a
chat ends; ...livechatoff... URLs have none yet, ...livechatdies... URLs fail the first time. A --print after_move:[ytdlpz:chat] template reports each
video as an ended stream, or as not a stream for ...plainvideo... URLs.
...upcoming... URLs first print yt-dlp's wait message. ...waiting... recordings keep
waiting for the stream and, like real yt-dlp, treat SIGINT as "check again" (only SIGTERM
stops them). ...gaps... recordings save the file but exit with yt-dlp's "Did not get any
data blocks" error, like a stream whose last fragments are gone when it ends.
With --match-filter (alignment downloads) ...live... and ...toolong... ids are skipped, like
videos the filter refuses. A --format starting with worstaudio (alignment) saves the video id
as the file's content, which the fake ffmpeg (fake_ffmpeg.py) turns into audio.
"""

import json
import os
import re
import signal
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PROGRESS = "[ytdlpz:progress]"
INFO = "[ytdlpz:info]"
FILE = "[ytdlpz:file]"
NFO = "[ytdlpz:nfo]"
CHAT = "[ytdlpz:chat]"
# %(name)s, %(a,b|default)s, %(upload_date>%Y)s, %(title).150B …
TEMPLATE_FIELD = re.compile(r"%\((?P<names>[\w,]+)(?:>(?P<format>[^|)]+))?(?:\|[^)]*)?\)[.\d]*[sB]")
FAKE_CHANNEL = "Fake channel"
FAKE_UPLOAD_DATE = "20261001"
TOTAL_BYTES = 1_000_000
TABS = ["Videos", "Live", "Shorts"]
# Upload time of every fake video: 2026-10-01 12:00 UTC.
UPLOADED_AT = 1790856000


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
    # Tests grow a playlist through FAKE_PLAYLIST_SIZE (yt-dlp runs inherit the env).
    size = int(os.environ.get("FAKE_PLAYLIST_SIZE", "3"))
    entries = [
        {"_type": "url", "id": f"item{n}", "title": f"Item {n}"} for n in range(1, size + 1)
    ]
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
        "timestamp": UPLOADED_AT,
    }
    if "members" in video_id:
        data["availability"] = "subscriber_only"
    if "upcoming" in video_id:
        data.update(live_status="is_upcoming", duration=None, release_timestamp=4_102_444_800)
    elif "ended" in video_id:
        data.update(live_status="was_live")
    elif "live" in video_id:
        data.update(live_status="is_live", duration=None)
        if "old" in video_id:  # live for 10 hours already
            data["release_timestamp"] = int(time.time()) - 10 * 3600
    emit(json.dumps(data))
    return 0


def videos_tab(url: str) -> int:
    if "broken" in url:
        return fail_json("This channel has no videos tab")
    entries: list[dict[str, str]] = []
    if "uploader" in url:
        entries = [{"id": "tab-new", "title": "Tab new"}, {"id": "tab-old", "title": "Tab old"}]
    emit(json.dumps({"id": "videos", "entries": entries}))
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
    if "/channel/" in url and url.endswith("/videos"):
        return videos_tab(url)
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


def fake_fields(args: list[str], title: str, video_id: str) -> dict[str, str]:
    fields = {
        "title": title,
        "id": video_id,
        "ext": "mp4",
        "channel": FAKE_CHANNEL,
        "upload_date": FAKE_UPLOAD_DATE,
    }
    # The fake videos have no release date, so air_date is the upload date.
    if any("(?P<air_date>" in value for value in values_of(args, "--parse-metadata")):
        fields["air_date"] = FAKE_UPLOAD_DATE
    return fields


def date_part(value: str, date_format: str) -> str:
    parts = {"%Y": value[:4], "%m": value[4:6], "%d": value[6:]}
    for code, part in parts.items():
        date_format = date_format.replace(code, part)
    return date_format


def output_name(args: list[str], title: str, video_id: str) -> str:
    templates = values_of(args, "--output")
    template = templates[-1] if templates else "%(title)s [%(id)s].%(ext)s"
    fields = fake_fields(args, title, video_id)

    def render(match: re.Match[str]) -> str:
        name = match["names"].split(",")[0]
        value = fields.get(name, "NA")
        return date_part(value, match["format"]) if match["format"] else value

    return TEMPLATE_FIELD.sub(render, template)


def emit_nfo(args: list[str], target: Path, title: str, video_id: str) -> None:
    if not any(value.startswith(f"after_move:{NFO}") for value in values_of(args, "--print")):
        return
    info = fake_fields(args, title, video_id) | {
        "filepath": str(target),
        "channel_id": "UCfakechannel",
        "description": "A fake video's description.",
        "duration": 125,
    }
    emit(NFO + json.dumps(info))


def emit_chat(args: list[str], target: Path, url: str) -> None:
    if any(value.startswith(f"after_move:{CHAT}") for value in values_of(args, "--print")):
        status = "not_live" if "plainvideo" in url else "was_live"
        info = {"filepath": str(target), "webpage_url": url, "live_status": status}
        emit(CHAT + json.dumps(info))


def text_action(offset_ms: int, text: str) -> dict[str, object]:
    renderer = {
        "message": {"runs": [{"text": text}]},
        "authorExternalChannelId": "UCfakeviewer",
    }
    item = {"liveChatTextMessageRenderer": renderer}
    actions = [{"addChatItemAction": {"item": item}}]
    return {"replayChatItemAction": {"actions": actions, "videoOffsetTimeMsec": str(offset_ms)}}


def paid_action(offset_ms: int, amount: str, text: str) -> dict[str, object]:
    renderer = {
        "purchaseAmountText": {"simpleText": amount},
        "message": {"runs": [{"text": text}]},
        "bodyBackgroundColor": 4278239141,
    }
    item = {"liveChatPaidMessageRenderer": renderer}
    actions = [{"addChatItemAction": {"item": item}}]
    return {"replayChatItemAction": {"actions": actions, "videoOffsetTimeMsec": str(offset_ms)}}


def live_line(index: int) -> dict[str, object]:
    """As yt-dlp writes live chat: one action per line, with the time of the comment."""
    usec = str(int(time.time() * 1_000_000))
    renderer = {
        "id": f"comment{index}",
        "timestampUsec": usec,
        "message": {"runs": [{"text": f"live comment {index}"}]},
    }
    item = {"liveChatTextMessageRenderer": renderer}
    actions = [{"addChatItemAction": {"item": item}}]
    return {"replayChatItemAction": {"actions": actions}, "videoOffsetTimeMsec": "0", "isLive": True}


def capture_chat(url: str, home: Path, name: str) -> int:
    if "livechatoff" in url:
        emit("[info] There are no subtitles for the requested languages")
        return 0
    target = home / Path(name).with_suffix(".live_chat.json.part")
    if "livechatdies" in url and name.startswith("chat-1"):
        target.write_text(json.dumps(live_line(0)) + "\n", encoding="utf-8")
        emit("ERROR: [fake] Unable to download video subtitles for live_chat")
        return 1
    with target.open("a", encoding="utf-8") as chat:
        for index in range(600):
            chat.write(json.dumps(live_line(index)) + "\n")
            chat.flush()
            time.sleep(0.1)
    target.rename(target.with_suffix(""))
    return 0


def save_chat(url: str, home: Path, name: str) -> int:
    if name.startswith("chat-"):
        return capture_chat(url, home, name)
    if "nochat" in url:
        emit("[info] There are no subtitles for the requested languages")
        return 0
    if "badchat" in url:
        emit("ERROR: [fake] Unable to download video subtitles for live_chat")
        return 1
    if "draggingchat" in url:
        time.sleep(60)
    lines = [
        text_action(1000, "first comment"),
        text_action(2000, "こんにちは"),
        paid_action(3000, "¥500", "thanks"),
    ]
    target = home / Path(name).with_suffix(".live_chat.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
    emit(f"[info] Writing video subtitles to: {target}")
    return 0


class Recording:
    """Stops a recording's loop on SIGINT, like yt-dlp finishing on Ctrl+C."""

    stopped = False

    @classmethod
    def stop(cls, *_args: object) -> None:
        cls.stopped = True


def wait_forever() -> None:
    """yt-dlp's --wait-for-video loop: Ctrl+C only makes it check the stream again."""
    signal.signal(signal.SIGINT, lambda *_args: emit("[wait] Interrupted by user"))
    while True:
        emit("[wait] Remaining time until next attempt: 00:04:59")
        time.sleep(0.1)


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


def replace_in_title(args: list[str], title: str) -> str:
    """--replace-in-metadata title REGEX REPLACE, as the VOD download passes it."""
    for index, arg in enumerate(args):
        if arg == "--replace-in-metadata" and args[index + 1] == "title":
            title = re.sub(args[index + 2], args[index + 3], title)
    return title


def main() -> int:
    args = sys.argv[1:]
    url = args[args.index("--") + 1]
    if "-J" in args:
        return metadata(url, args)
    video_id = video_id_of(url)
    title = replace_in_title(args, f"Fake video {video_id}")
    if "--simulate" in args:
        return simulate(url, title)
    emit("[fake] args: " + " ".join(args[: args.index("--")]))
    report_cookies(args)
    home = Path(next(v for v in values_of(args, "--paths") if v.startswith("home:"))[5:])

    if "--skip-download" in args and "--write-subs" in args:
        return save_chat(url, home, output_name(args, title, video_id).replace("%%", "%"))
    if "fail" in url:
        emit("ERROR: [fake] This video is unavailable")
        return 1
    if any("blocked" in proxy for proxy in values_of(args, "--proxy")):
        emit(f"ERROR: [youtube] {video_id}: Sign in to confirm you're not a bot")
        return 1
    if "--match-filter" in args and ("live" in video_id or "toolong" in video_id):
        emit(f"[download] {title} does not pass filter ({values_of(args, '--match-filter')[0]})")
        return 0
    if "stubborn" in url:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    steps, delay = (600, 0.1) if "slow" in url or "stubborn" in url else (5, 0.05)
    live = "--wait-for-video" in args
    if live:
        signal.signal(signal.SIGINT, Recording.stop)
    if live and "upcoming" in url:
        emit("[wait] Waiting for the stream to start")
    if live and "waiting" in url:
        wait_forever()

    emit(INFO + json.dumps({"id": video_id, "title": title, "webpage_url": url}))
    for step in range(1, steps + 1):
        if Recording.stopped:
            break
        emit_progress(TOTAL_BYTES * step // steps, steps - step, args)
        time.sleep(delay)

    target = home / output_name(args, title, video_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    audio_only = any(f.startswith("worstaudio") for f in values_of(args, "--format"))
    target.write_bytes(video_id.encode() if audio_only else b"fake video")
    if "--write-thumbnail" in args:
        target.with_suffix(".jpg").write_bytes(b"fake thumbnail")
    emit(PROGRESS + json.dumps({"status": "finished", "downloaded_bytes": TOTAL_BYTES}))
    emit(FILE + json.dumps(str(target)))
    emit_nfo(args, target, title, video_id)
    emit_chat(args, target, url)
    if live and "expiring" in url and "--live-from-start" in args:
        # YouTube's links expire after about 6 h; yt-dlp often can't renew them.
        for _ in range(3):
            emit("WARNING: [youtube] Cannot find refreshed url for format 303; Retrying...")
    if live and "gaps" in url:
        emit("ERROR: Did not get any data blocks")
        return 1
    emit("[fake] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
