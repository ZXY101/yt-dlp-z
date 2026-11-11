"""An alignment job's state, as the API reports it."""

import asyncio
from dataclasses import dataclass, field
from enum import StrEnum


class AlignState(StrEnum):
    DOWNLOADING = "downloading"
    ANALYSING = "analysing"
    DONE = "done"
    FAILED = "failed"


class AlignBusyError(Exception):
    pass


@dataclass
class AlignJob:
    id: str
    urls: list[str]
    last_seen: float
    state: AlignState = AlignState.DOWNLOADING
    error: str | None = None
    offsets: dict[str, float | None] = field(default_factory=dict)
    confidence: dict[str, float] = field(default_factory=dict)
    downloads: list[float] = field(default_factory=list)
    task: asyncio.Task[None] | None = None

    @property
    def running(self) -> bool:
        return self.state in {AlignState.DOWNLOADING, AlignState.ANALYSING}

    @property
    def progress(self) -> float:
        """Downloads are most of the time a job takes; analysing is quick."""
        if not self.running:
            return 1.0
        if self.state is AlignState.ANALYSING:
            return 0.95
        return 0.9 * sum(self.downloads) / max(1, len(self.downloads))
