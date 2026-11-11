"""Speech-like test audio: bursts of noise with gaps, like syllables and pauses."""

from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from yt_dlp_z.services.align.envelope import SAMPLE_RATE

AMPLITUDE = 8000


def event(seconds: float, seed: int = 1) -> NDArray[np.float64]:
    rng = np.random.default_rng(seed)
    total = int(seconds * SAMPLE_RATE)
    loudness = np.zeros(total)
    position = 0
    while position < total:
        length = int(rng.uniform(0.08, 1.2) * SAMPLE_RATE)
        loudness[position : position + length] = rng.uniform(0.2, 1.0)
        position += length + int(rng.uniform(0.05, 0.8) * SAMPLE_RATE)
    noise: NDArray[np.float64] = loudness * rng.standard_normal(total)
    return noise


def recording(
    source: NDArray[np.float64], start: float, seconds: float, *, seed: int = 2
) -> NDArray[np.int16]:
    """source from `start` for `seconds`, with its own quieter background noise and level.
    Two recordings starting at s1 and s2 are s1 - s2 seconds apart."""
    rng = np.random.default_rng(seed)
    first = int(start * SAMPLE_RATE)
    clip = source[first : first + int(seconds * SAMPLE_RATE)]
    mixed = rng.uniform(0.5, 1.0) * clip + 0.3 * rng.standard_normal(len(clip))
    return np.clip(mixed * AMPLITUDE / 3, -32768, 32767).astype("<i2")


def write(path: Path, samples: NDArray[np.int16]) -> Path:
    path.write_bytes(samples.tobytes())
    return path
