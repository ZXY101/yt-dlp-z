"""Decoded audio on disk and the loudness envelopes the coarse match works on.

Audio is raw 16-bit mono PCM at SAMPLE_RATE (what decode.py writes). Files can hold
12 hours, so they are memory-mapped and read in chunks, never loaded whole.
"""

from pathlib import Path

import numpy as np
from numpy.typing import NDArray

SAMPLE_RATE = 2000
ENVELOPE_RATE = 100
BLOCK = SAMPLE_RATE // ENVELOPE_RATE
# Blocks per chunk read from the file: about 8 MB of float32 at a time.
CHUNK_BLOCKS = 100_000

Samples = NDArray[np.int16]
Envelope = NDArray[np.float32]


def read_pcm(path: Path) -> Samples:
    if path.stat().st_size < 2:  # noqa: PLR2004  (one 16-bit sample)
        # numpy can't map an empty file.
        return np.zeros(0, dtype=np.int16)
    return np.memmap(path, dtype="<i2", mode="r")


def loudness_envelope(samples: Samples) -> Envelope:
    """Log loudness of each BLOCK of samples, ENVELOPE_RATE values per second."""
    blocks = len(samples) // BLOCK
    envelope = np.empty(blocks, dtype=np.float32)
    for first in range(0, blocks, CHUNK_BLOCKS):
        last = min(first + CHUNK_BLOCKS, blocks)
        chunk = np.asarray(samples[first * BLOCK : last * BLOCK], dtype=np.float32)
        power = np.mean(np.square(chunk.reshape(-1, BLOCK)), axis=1)
        envelope[first:last] = np.log1p(np.sqrt(power))
    return envelope


def downsample(envelope: Envelope, factor: int) -> Envelope:
    usable = len(envelope) // factor * factor
    reduced: Envelope = envelope[:usable].reshape(-1, factor).mean(axis=1, dtype=np.float32)
    return reduced


def _moving_mean(values: Envelope, window: int) -> Envelope:
    padded = np.concatenate(([0.0], np.cumsum(values, dtype=np.float64)))
    index = np.arange(len(values))
    low = np.clip(index - window // 2, 0, len(values))
    high = np.clip(index + window // 2 + 1, 0, len(values))
    means: Envelope = ((padded[high] - padded[low]) / (high - low)).astype(np.float32)
    return means


def normalise(envelope: Envelope, window: int) -> Envelope:
    """Removes slow level changes (different mic gain, music fading in) over `window`
    values and scales to unit variance, so two streams' envelopes are comparable."""
    if len(envelope) == 0:
        return envelope
    detail = envelope - _moving_mean(envelope, window)
    spread = float(np.std(detail))
    if spread == 0:
        return np.zeros_like(envelope)
    result: Envelope = (detail / spread).astype(np.float32)
    return result
