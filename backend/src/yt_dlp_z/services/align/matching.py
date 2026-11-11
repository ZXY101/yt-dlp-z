"""Finds how far apart two recordings of the same event are.

Three steps, each on less data than a whole-file FFT at full rate would need:
1. coarse: correlate 10 Hz loudness envelopes over the whole overlap; keep a few best lags
2. refine: test the lags around each at 100 Hz
3. check: on several short windows of the 2 kHz audio, find the exact lag; the share of
   windows that agree is the confidence, and the best-checked candidate wins.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from yt_dlp_z.services.align.correlate import (
    AUDIO_WEIGHT,
    ENVELOPE_WEIGHT,
    best_lags,
    lag_range,
    overlap_slices,
    pearson,
    weighted_correlation,
)
from yt_dlp_z.services.align.envelope import (
    BLOCK,
    ENVELOPE_RATE,
    SAMPLE_RATE,
    Envelope,
    Samples,
    downsample,
    loudness_envelope,
    normalise,
    read_pcm,
)

COARSE_FACTOR = 10
COARSE_RATE = ENVELOPE_RATE // COARSE_FACTOR
MIN_OVERLAP_SECONDS = 60
CANDIDATES = 3
NORMALISE_SECONDS = 10
REFINE_SECONDS = 0.3
WINDOWS = 8
WINDOW_SECONDS = 20
SEARCH_SECONDS = 0.25
# Windows within 5 ms of the median lag agree with it.
AGREE_SAMPLES = 10
# A window's peak must beat the next best peak by this much to count.
PEAK_RATIO = 1.5
PEAK_WIDTH = 4
# RMS of 16-bit samples below which a window is treated as silence and skipped.
SILENCE_RMS = 30.0


@dataclass(frozen=True)
class Match:
    # Seconds by which the second recording's content is later than the first's.
    offset: float
    # Share of checked windows that agree with the offset (0 to 1).
    confidence: float


def match_pair(first: Path, second: Path) -> Match | None:
    """None when the recordings don't overlap by at least MIN_OVERLAP_SECONDS."""
    a = read_pcm(first)
    b = read_pcm(second)
    envelope_a = loudness_envelope(a)
    envelope_b = loudness_envelope(b)
    candidates = _coarse_candidates(envelope_a, envelope_b)
    window = NORMALISE_SECONDS * ENVELOPE_RATE
    fine_a = normalise(envelope_a, window)
    fine_b = normalise(envelope_b, window)
    matches = [_check(a, b, _refine(fine_a, fine_b, lag)) for lag in candidates]
    return max(matches, key=lambda match: match.confidence, default=None)


def _coarse_candidates(envelope_a: Envelope, envelope_b: Envelope) -> list[int]:
    """Best lags in envelope values (ENVELOPE_RATE per second)."""
    window = NORMALISE_SECONDS * COARSE_RATE
    coarse_a = normalise(downsample(envelope_a, COARSE_FACTOR), window)
    coarse_b = normalise(downsample(envelope_b, COARSE_FACTOR), window)
    lags = lag_range(len(coarse_a), len(coarse_b), MIN_OVERLAP_SECONDS * COARSE_RATE)
    if lags[0] > lags[1]:
        return []
    corr = weighted_correlation(coarse_a, coarse_b, ENVELOPE_WEIGHT)
    found = best_lags(corr, lags, CANDIDATES, spacing=2 * COARSE_RATE)
    return [lag * COARSE_FACTOR for lag in found]


def _refine(envelope_a: Envelope, envelope_b: Envelope, lag: int) -> int:
    reach = int(REFINE_SECONDS * ENVELOPE_RATE)
    scores = {
        candidate: pearson(*overlap_slices(envelope_a, envelope_b, candidate))
        for candidate in range(lag - reach, lag + reach + 1)
    }
    return max(scores, key=scores.__getitem__)


def _window_starts(a: Samples, b: Samples, lag: int) -> list[int]:
    window = WINDOW_SECONDS * SAMPLE_RATE
    margin = int(SEARCH_SECONDS * SAMPLE_RATE)
    first = max(0, margin - lag)
    last = min(len(a), len(b) - lag - margin) - window
    if last < first:
        return []
    return sorted({int(start) for start in np.linspace(first, last, WINDOWS)})


def _check(a: Samples, b: Samples, envelope_lag: int) -> Match:
    lag = envelope_lag * BLOCK
    window = WINDOW_SECONDS * SAMPLE_RATE
    margin = int(SEARCH_SECONDS * SAMPLE_RATE)
    deltas: list[int] = []
    tried = 0
    for start in _window_starts(a, b, lag):
        segment_a = np.asarray(a[start : start + window], dtype=np.float64)
        if np.sqrt(np.mean(np.square(segment_a))) < SILENCE_RMS:
            continue
        tried += 1
        b_start = start + lag - margin
        segment_b = np.asarray(b[b_start : b_start + window + 2 * margin], dtype=np.float64)
        delta = _window_delta(segment_a, segment_b, margin)
        if delta is not None:
            deltas.append(delta)
    return _combine(lag, deltas, tried)


def _window_delta(segment_a: np.ndarray, segment_b: np.ndarray, margin: int) -> int | None:
    """The lag within ±margin at which segment_b (cut margin early) matches segment_a."""
    values = weighted_correlation(segment_a, segment_b, AUDIO_WEIGHT)[: 2 * margin + 1]
    best = int(np.argmax(values))
    others = values.copy()
    others[max(0, best - PEAK_WIDTH) : best + PEAK_WIDTH + 1] = -np.inf
    runner_up = float(np.max(others))
    if runner_up > 0 and values[best] < PEAK_RATIO * runner_up:
        return None
    return best - margin


def _combine(lag: int, deltas: list[int], tried: int) -> Match:
    if not deltas:
        return Match(offset=lag / SAMPLE_RATE, confidence=0.0)
    median = float(np.median(deltas))
    agreeing = [delta for delta in deltas if abs(delta - median) <= AGREE_SAMPLES]
    offset = (lag + float(np.mean(agreeing))) / SAMPLE_RATE
    return Match(offset=offset, confidence=len(agreeing) / tried)
