"""Background poller: checks each enabled subscription when its interval is up."""

import asyncio
import functools
import logging
import random
from datetime import datetime, timedelta

from sqlalchemy import select

from yt_dlp_z.db.models.job import utcnow
from yt_dlp_z.db.models.subscription import Subscription
from yt_dlp_z.services.watch.checker import check_subscription
from yt_dlp_z.services.watch.enqueue import WatchContext

logger = logging.getLogger(__name__)

TICK_SECONDS = 30
# Spreads checks out so channels added together don't keep polling at the same moment.
MAX_JITTER = 0.1


def is_due(last_check: datetime | None, poll_minutes: int, jitter: float, now: datetime) -> bool:
    if last_check is None:
        return True
    if last_check.tzinfo is None:  # SQLite drops the timezone; stored values are UTC.
        last_check = last_check.replace(tzinfo=now.tzinfo)
    return now >= last_check + timedelta(minutes=poll_minutes * (1 + jitter))


class SubscriptionWatcher:
    def __init__(self, context: WatchContext) -> None:
        self._context = context
        self._loop: asyncio.Task[None] | None = None
        self._checks: dict[int, asyncio.Task[None]] = {}
        # Failed checks don't move last_checked_at, so the attempt time is kept here
        # to stop a broken channel from being retried on every tick.
        self._last_attempt: dict[int, datetime] = {}
        self._jitter: dict[int, float] = {}

    def start(self) -> None:
        self._loop = asyncio.create_task(self._run())

    async def stop(self) -> None:
        tasks = [*self._checks.values(), *([self._loop] if self._loop else [])]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def stop_checks(self) -> None:
        """Cancels running checks and forgets attempt times (used by the test reset)."""
        checks = list(self._checks.values())
        for task in checks:
            task.cancel()
        await asyncio.gather(*checks, return_exceptions=True)
        self._last_attempt.clear()

    def is_checking(self, subscription_id: int) -> bool:
        return subscription_id in self._checks

    def check_now(self, subscription_id: int) -> asyncio.Task[None]:
        """Starts a check unless one is running; returns the running check either way."""
        running = self._checks.get(subscription_id)
        if running is not None:
            return running
        task = asyncio.create_task(self._check(subscription_id))
        self._checks[subscription_id] = task
        task.add_done_callback(functools.partial(self._forget, subscription_id))
        return task

    def _forget(self, subscription_id: int, task: asyncio.Task[None]) -> None:
        if self._checks.get(subscription_id) is task:
            del self._checks[subscription_id]

    async def _check(self, subscription_id: int) -> None:
        self._last_attempt[subscription_id] = utcnow()
        self._jitter[subscription_id] = random.uniform(0, MAX_JITTER)  # noqa: S311  (not crypto)
        try:
            await check_subscription(self._context, subscription_id)
        except Exception:
            logger.exception("Checking subscription %s crashed", subscription_id)

    async def _run(self) -> None:
        while True:
            try:
                await self._check_due()
            except Exception:
                logger.exception("The subscription poller crashed; retrying next tick")
            await asyncio.sleep(TICK_SECONDS)

    async def _check_due(self) -> None:
        """Checks due subscriptions one after another, to keep the request rate low."""
        async with self._context.session_factory() as session:
            result = await session.execute(select(Subscription).where(Subscription.enabled))
            subscriptions = list(result.scalars())
        now = utcnow()
        for subscription in subscriptions:
            last_check = self._last_attempt.get(subscription.id, subscription.last_checked_at)
            jitter = self._jitter.get(subscription.id, 0.0)
            if is_due(last_check, subscription.poll_minutes, jitter, now):
                await self.check_now(subscription.id)
