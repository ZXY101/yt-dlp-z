#!/usr/bin/env python3
"""Stand-in for ffmpeg's alignment decode (backend services/align/fetch.py).

Reads its input (pipe:0, which the fake yt-dlp fills with the video id) and writes 10 minutes
of raw 16-bit PCM at 2 kHz for it:
  ...align-<N>...  speech-like audio of one shared event, starting N seconds into it, so
                   align-60 and align-30 are 30 s apart (the second is 30 s later)
  ...unrelated...  audio of a different event (no match)
  ...nodecode...   fails like unreadable input
  (no input)       fails like real ffmpeg on an empty pipe
Never touches the network.
"""

import re
import sys
from pathlib import Path

import numpy as np

RATE = 2000
SECONDS = 600
EVENT_SECONDS = 1500


def event(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    total = EVENT_SECONDS * RATE
    loudness = np.zeros(total)
    position = 0
    while position < total:
        length = int(rng.uniform(0.08, 1.2) * RATE)
        loudness[position : position + length] = rng.uniform(0.2, 1.0)
        position += length + int(rng.uniform(0.05, 0.8) * RATE)
    return loudness * rng.standard_normal(total)


def main() -> int:
    args = sys.argv[1:]
    source = args[args.index("-i") + 1]
    target = Path(args[-1])
    data = sys.stdin.buffer.read() if source == "pipe:0" else Path(source).read_bytes()
    video_id = data.decode(errors="replace")
    if not data or "nodecode" in video_id:
        print(f"{source}: Invalid data found when processing input", file=sys.stderr)
        return 1
    start_match = re.search(r"align-(\d+)", video_id)
    start = int(start_match[1]) if start_match else 0
    shared = event(seed=99 if "unrelated" in video_id else 1)
    clip = shared[start * RATE : (start + SECONDS) * RATE]
    seed = int.from_bytes(video_id.encode()[-8:], "big")
    noise = np.random.default_rng(seed).standard_normal(len(clip))
    samples = np.clip((clip + 0.3 * noise) * 2500, -32768, 32767).astype("<i2")
    target.write_bytes(samples.tobytes())
    return 0


if __name__ == "__main__":
    sys.exit(main())
