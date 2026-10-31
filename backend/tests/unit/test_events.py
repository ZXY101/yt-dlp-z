from yt_dlp_z.services.events import QUEUE_SIZE, EventHub


def test_publish_reaches_every_subscriber() -> None:
    hub = EventHub()
    first, second = hub.subscribe(), hub.subscribe()
    hub.publish({"type": "job"})
    assert first.get_nowait() == second.get_nowait() == {"type": "job"}


def test_unsubscribed_queues_get_nothing() -> None:
    hub = EventHub()
    queue = hub.subscribe()
    hub.unsubscribe(queue)
    hub.publish({"type": "job"})
    assert queue.empty()


def test_stuck_subscribers_are_dropped() -> None:
    hub = EventHub()
    stuck = hub.subscribe()
    for number in range(QUEUE_SIZE + 1):
        hub.publish({"n": number})
    hub.publish({"n": "after"})
    assert stuck.qsize() == QUEUE_SIZE
    assert stuck not in hub._subscribers


def test_listeners_get_every_event() -> None:
    hub = EventHub()
    seen: list[dict[str, object]] = []
    hub.listen(seen.append)
    hub.publish({"type": "job"})
    assert seen == [{"type": "job"}]
