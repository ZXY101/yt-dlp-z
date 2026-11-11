"""An alignment job's state, as the API reports it."""

import asyncio
from dataclasses import dataclass, field
from enum import StrEnum


class AlignState(StrEnum):
    DOWNLOADING = "downloading"
    ANALYSING = "analysing"
    DONE = "done"
    FAILED = "failed"


class StreamStage(StrEnum):
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    READY = "ready"


class AlignBusyError(Exception):
    pass


@dataclass
class StreamProgress:
    """One link's part of a job, so clients can show what's happening."""

    url: str
    stage: StreamStage = StreamStage.DOWNLOADING
    # Download progress (0 to 1).
    downloaded: float = 0.0

    @property
    def share(self) -> float:
        """How much of this link's work is done (0 to 1); converting is the last tenth."""
        if self.stage is StreamStage.READY:
            return 1.0
        if self.stage is StreamStage.CONVERTING:
            return 0.9
        return 0.9 * self.downloaded


@dataclass
class AlignJob:
    id: str
    urls: list[str]
    last_seen: float
    state: AlignState = AlignState.DOWNLOADING
    error: str | None = None
    offsets: dict[str, float | None] = field(default_factory=dict)
    confidence: dict[str, float] = field(default_factory=dict)
    streams: list[StreamProgress] = field(default_factory=list)
    task: asyncio.Task[None] | None = None

    @property
    def running(self) -> bool:
        return self.state in {AlignState.DOWNLOADING, AlignState.ANALYSING}

    @property
    def progress(self) -> float:
        """Getting the audio is most of the time a job takes; analysing is quick."""
        if not self.running:
            return 1.0
        if self.state is AlignState.ANALYSING:
            return 0.95
        return 0.9 * sum(stream.share for stream in self.streams) / max(1, len(self.streams))
