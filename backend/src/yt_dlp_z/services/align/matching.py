"""Finds how far apart two recordings of the same event are.

Each streamer's copy of the shared sound (voices over Discord, game audio) goes through
different codecs, mixes and levels, so the waveforms don't match, but loudness over time
does. All steps work on loudness envelopes:
1. coarse: correlate 10 Hz envelopes over the whole overlap; keep a few best lags
2. refine: test the lags around each at 100 Hz over the whole overlap (the offset)
3. check: score the offset on several one-minute windows spread over the overlap; the
   share of windows that clearly correlate is the confidence, and the best candidate wins.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from yt_dlp_z.services.align.correlate import (
    ENVELOPE_WEIGHT,
    best_lags,
    lag_range,
    overlap_slices,
    pearson,
    weighted_correlation,
)
from yt_dlp_z.services.align.envelope import (
    ENVELOPE_RATE,
    Envelope,
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
WINDOWS = 12
WINDOW_SECONDS = 60
# The lag inside one window wanders by a few tenths of a second (network delay between
# streamers), so each window may find its best match this far from the offset.
SEARCH_SECONDS = 1.0
# Correlation a window needs to count as matching. Real collab pairs score 0.4 to 0.6,
# wrong offsets around 0.1.
MATCH_SCORE = 0.25


@dataclass(frozen=True)
class Match:
    # Seconds by which the second recording's content is later than the first's.
    offset: float
    # Share of checked windows that match at the offset (0 to 1).
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
    matches = [_check(fine_a, fine_b, _refine(fine_a, fine_b, lag)) for lag in candidates]
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


def _window_starts(len_a: int, len_b: int, lag: int) -> list[int]:
    window = WINDOW_SECONDS * ENVELOPE_RATE
    margin = int(SEARCH_SECONDS * ENVELOPE_RATE)
    first = max(0, margin - lag)
    last = min(len_a, len_b - lag - margin) - window
    if last < first:
        return []
    return sorted({int(start) for start in np.linspace(first, last, WINDOWS)})


def _window_score(segment: Envelope, envelope_b: Envelope, start_b: int) -> float:
    """Best correlation of segment with envelope_b near start_b (± SEARCH_SECONDS)."""
    margin = int(SEARCH_SECONDS * ENVELOPE_RATE)
    window = len(segment)
    return max(
        pearson(segment, envelope_b[start_b + shift : start_b + shift + window])
        for shift in range(-margin, margin + 1)
    )


def _check(envelope_a: Envelope, envelope_b: Envelope, lag: int) -> Match:
    window = WINDOW_SECONDS * ENVELOPE_RATE
    starts = _window_starts(len(envelope_a), len(envelope_b), lag)
    scores = [
        _window_score(envelope_a[start : start + window], envelope_b, start + lag)
        for start in starts
    ]
    matching = sum(score >= MATCH_SCORE for score in scores)
    confidence = matching / len(scores) if scores else 0.0
    return Match(offset=lag / ENVELOPE_RATE, confidence=confidence)
