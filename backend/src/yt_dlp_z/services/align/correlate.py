"""Cross-correlation helpers. A lag k means b's content is k samples later than a's:
b[n + k] matches a[n]."""

import numpy as np
from numpy.typing import NDArray

Signal = NDArray[np.floating]
# Partial whitening (PHAT-beta): sharpens the peak without the noise full PHAT (1.0)
# gives on loudness envelopes, which carry little detail per value.
ENVELOPE_WEIGHT = 0.7
EPSILON = 1e-12


def _fft_size(length: int) -> int:
    return 1 << max(0, length - 1).bit_length()


def weighted_correlation(a: Signal, b: Signal, weight: float) -> NDArray[np.float64]:
    """corr[k] = sum of a[n] * b[n + k], with negative lags at the end (corr[-1] is k=-1).
    The spectrum is divided by its magnitude**weight, which sharpens the peak."""
    size = _fft_size(len(a) + len(b))
    spectrum = np.conj(np.fft.rfft(a, size)) * np.fft.rfft(b, size)
    spectrum /= np.power(np.abs(spectrum), weight) + EPSILON
    corr: NDArray[np.float64] = np.fft.irfft(spectrum, size).astype(np.float64)
    return corr


def lag_range(len_a: int, len_b: int, min_overlap: int) -> tuple[int, int]:
    """The lags (inclusive) at which a and b share at least min_overlap samples."""
    return min_overlap - len_a, len_b - min_overlap


def best_lags(
    corr: NDArray[np.float64], lags: tuple[int, int], count: int, spacing: int
) -> list[int]:
    """The `count` highest peaks among lags[0]..lags[1], at least `spacing` apart."""
    low, high = lags
    if low > high:
        return []
    candidates = np.arange(low, high + 1)
    values = corr[candidates % len(corr)].copy()
    found: list[int] = []
    while len(found) < count and np.isfinite(values).any():
        best = int(np.argmax(values))
        found.append(int(candidates[best]))
        values[max(0, best - spacing) : best + spacing + 1] = -np.inf
    return found


def overlap_slices(a: Signal, b: Signal, lag: int) -> tuple[Signal, Signal]:
    start = max(0, -lag)
    end = min(len(a), len(b) - lag)
    return a[start:end], b[start + lag : end + lag]


def pearson(a: Signal, b: Signal) -> float:
    if len(a) < 2:  # noqa: PLR2004  (a correlation needs two points)
        return 0.0
    a_centred = a - a.mean()
    b_centred = b - b.mean()
    scale = float(np.sqrt(np.dot(a_centred, a_centred) * np.dot(b_centred, b_centred)))
    return float(np.dot(a_centred, b_centred)) / scale if scale > 0 else 0.0
