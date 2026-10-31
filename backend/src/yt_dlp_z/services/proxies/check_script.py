"""Opens two pages through a proxy and prints the result as JSON.

Runs as its own process, like services/ytdlp/schema_dump.py, so the server never imports
yt-dlp. It uses yt-dlp's own networking, so a proxy that passes works for downloads too.
The proxy address comes on stdin: it may hold a password, and the command line is
visible to other processes."""

import json
import re
import sys
from typing import Any

# Answers with the IP and country it was reached from ("ip=…", "loc=…" lines).
TRACE_URL = "https://www.cloudflare.com/cdn-cgi/trace"
YOUTUBE_URL = "https://www.youtube.com/generate_204"
TIMEOUT_SECONDS = 20
# "SocksHTTPSConnection(host='www.cloudflare.com', port=443): " before the actual reason.
CONNECTION_PREFIX = re.compile(r"^\w+\(host='[^']*', port=\d+\): ")


def exit_ip(trace: str) -> str | None:
    fields = dict(line.split("=", 1) for line in trace.splitlines() if "=" in line)
    ip = fields.get("ip")
    if ip is None:
        return None
    location = fields.get("loc")
    return f"{ip} ({location})" if location else ip


def short_error(error: BaseException) -> str:
    return CONNECTION_PREFIX.sub("", str(error)) or type(error).__name__


def check(proxy: str) -> dict[str, Any]:
    from yt_dlp import YoutubeDL  # noqa: PLC0415  (kept out of module scope; see docstring)

    params = {"proxy": proxy, "quiet": True, "no_warnings": True, "socket_timeout": TIMEOUT_SECONDS}
    try:
        with YoutubeDL(params) as ydl:
            trace = ydl.urlopen(TRACE_URL).read().decode(errors="replace")
            ydl.urlopen(YOUTUBE_URL).read()
    # Any failure is the answer.
    except Exception as error:
        return {"ok": False, "exit_ip": None, "error": short_error(error)}
    return {"ok": True, "exit_ip": exit_ip(trace), "error": None}


def main() -> None:
    json.dump(check(sys.stdin.read().strip()), sys.stdout)


if __name__ == "__main__":
    main()
