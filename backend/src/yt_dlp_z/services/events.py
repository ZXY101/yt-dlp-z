import asyncio
from typing import Any

Event = dict[str, Any]
QUEUE_SIZE = 256


class EventHub:
    """Fans server events out to connected WebSocket clients."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[Event]] = set()

    def subscribe(self) -> asyncio.Queue[Event]:
        queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=QUEUE_SIZE)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[Event]) -> None:
        self._subscribers.discard(queue)

    def publish(self, event: Event) -> None:
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # A client this far behind is stuck; dropping it makes it reconnect
                # and refetch rather than slowly leaking memory.
                self.unsubscribe(queue)
