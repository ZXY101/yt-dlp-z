from collections.abc import Sequence

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.subscription import Subscription
from yt_dlp_z.db.models.video import Video
from yt_dlp_z.schemas.subscriptions import SubscriptionCreate, SubscriptionUpdate
from yt_dlp_z.services.app_settings import get_max_subscriptions
from yt_dlp_z.services.watch.channel import Channel

RECENT_VIDEOS = 50


class SubscriptionLimitError(ValueError):
    pass


class DuplicateSubscriptionError(ValueError):
    pass


async def list_subscriptions(session: AsyncSession) -> Sequence[Subscription]:
    result = await session.execute(select(Subscription).order_by(Subscription.name))
    return result.scalars().all()


async def get_subscription(session: AsyncSession, subscription_id: int) -> Subscription | None:
    return await session.get(Subscription, subscription_id)


async def check_limit(session: AsyncSession) -> None:
    """The limit counts every subscription, paused ones too."""
    count = await session.scalar(select(func.count()).select_from(Subscription)) or 0
    limit = await get_max_subscriptions(session)
    if count >= limit:
        raise SubscriptionLimitError(
            f"You're watching {count} of {limit} channels. Raise the limit in Settings first."
        )


async def check_not_subscribed(session: AsyncSession, channel_id: str) -> None:
    existing = await session.scalar(
        select(Subscription.name).where(Subscription.channel_id == channel_id)
    )
    if existing is not None:
        raise DuplicateSubscriptionError(f"You already watch {existing}")


def _apply(subscription: Subscription, values: SubscriptionUpdate) -> None:
    subscription.preset_id = values.preset_id
    subscription.stream_preset_id = values.stream_preset_id
    subscription.cookie_id = values.cookie_id
    subscription.output_dir = values.output_dir
    subscription.filters = values.filters.model_dump(mode="json")
    subscription.poll_minutes = values.poll_minutes
    subscription.enabled = values.enabled


async def create_subscription(
    session: AsyncSession, channel: Channel, values: SubscriptionCreate
) -> Subscription:
    subscription = Subscription(
        channel_id=channel.channel_id,
        name=channel.name,
        url=channel.url,
        backfill=values.backfill,
    )
    _apply(subscription, values)
    session.add(subscription)
    await session.commit()
    await session.refresh(subscription)
    return subscription


async def update_subscription(
    session: AsyncSession, subscription: Subscription, values: SubscriptionUpdate
) -> Subscription:
    _apply(subscription, values)
    await session.commit()
    await session.refresh(subscription)
    return subscription


async def delete_subscription(session: AsyncSession, subscription: Subscription) -> None:
    """Forgets the channel and its seen videos. Downloads stay in the queue history."""
    # SQLite doesn't enforce the cascade unless foreign keys are switched on per connection.
    await session.execute(delete(Video).where(Video.subscription_id == subscription.id))
    await session.delete(subscription)
    await session.commit()


async def list_videos(session: AsyncSession, subscription_id: int) -> Sequence[Video]:
    result = await session.execute(
        select(Video)
        .where(Video.subscription_id == subscription_id)
        .order_by(Video.published_at.desc(), Video.id.desc())
        .limit(RECENT_VIDEOS)
    )
    return result.scalars().all()


async def unlink_preset(session: AsyncSession, preset_id: int) -> None:
    await session.execute(
        update(Subscription).where(Subscription.preset_id == preset_id).values(preset_id=None)
    )
    await session.execute(
        update(Subscription)
        .where(Subscription.stream_preset_id == preset_id)
        .values(stream_preset_id=None)
    )


async def unlink_cookie_file(session: AsyncSession, cookie_id: int) -> None:
    await session.execute(
        update(Subscription).where(Subscription.cookie_id == cookie_id).values(cookie_id=None)
    )
