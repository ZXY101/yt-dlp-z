from pathlib import Path

import numpy as np
import pytest

from tests.synthetic_audio import event, recording, write
from yt_dlp_z.services.align.envelope import normalise, read_pcm
from yt_dlp_z.services.align.matching import match_pair

SOURCE = event(1500)


def pair(
    tmp_path: Path, first: tuple[float, float], second: tuple[float, float]
) -> tuple[Path, Path]:
    a = write(tmp_path / "a.pcm", recording(SOURCE, *first, seed=3))
    b = write(tmp_path / "b.pcm", recording(SOURCE, *second, seed=4))
    return a, b


@pytest.mark.parametrize(
    ("first", "second", "offset"),
    [
        ((60, 600), (30, 900), 30.0),
        ((30, 1000), (400.37, 600), -370.37),
        ((0, 300), (0, 300), 0.0),
    ],
)
def test_finds_the_offset(
    tmp_path: Path, first: tuple[float, float], second: tuple[float, float], offset: float
) -> None:
    match = match_pair(*pair(tmp_path, first, second))
    assert match is not None
    assert match.offset == pytest.approx(offset, abs=0.02)
    assert match.confidence == 1.0


def test_recordings_that_dont_overlap_get_low_confidence(tmp_path: Path) -> None:
    match = match_pair(*pair(tmp_path, (100, 300), (1100, 300)))
    assert match is not None
    assert match.confidence < 0.5


def test_recordings_shorter_than_the_minimum_overlap_have_no_match(tmp_path: Path) -> None:
    assert match_pair(*pair(tmp_path, (0, 30), (0, 30))) is None


def test_silence_has_no_confident_match(tmp_path: Path) -> None:
    silent = np.zeros(300 * 2000, dtype="<i2")
    a = write(tmp_path / "a.pcm", silent)
    b = write(tmp_path / "b.pcm", silent)
    match = match_pair(a, b)
    assert match is not None
    assert match.confidence == 0.0


def test_empty_files_read_as_no_samples(tmp_path: Path) -> None:
    empty = tmp_path / "empty.pcm"
    empty.write_bytes(b"")
    assert len(read_pcm(empty)) == 0
    assert match_pair(empty, empty) is None


def test_normalise_handles_flat_and_empty_envelopes() -> None:
    flat = np.ones(100, dtype=np.float32)
    assert not normalise(flat, 10).any()
    assert len(normalise(np.zeros(0, dtype=np.float32), 10)) == 0
