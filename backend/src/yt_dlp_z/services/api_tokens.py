import hashlib
import secrets
from collections.abc import Sequence
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from yt_dlp_z.db.models.api_token import ApiToken, TokenScope
from yt_dlp_z.db.models.job import utcnow

# Makes a leaked token recognisable to secret scanners and to people.
TOKEN_PREFIX = "ytz_"  # noqa: S105  (a label, not a secret)
# Agents call often; one write per few minutes is enough for "last used".
LAST_USED_PRECISION = timedelta(minutes=5)


class DuplicateTokenNameError(ValueError):
    pass


def _hash_token(token: str) -> str:
    # A fast hash is safe here: tokens are 256 random bits, so guessing can't work.
    return hashlib.sha256(token.encode()).hexdigest()


async def list_tokens(session: AsyncSession) -> Sequence[ApiToken]:
    result = await session.execute(select(ApiToken).order_by(ApiToken.name))
    return result.scalars().all()


async def create_token(
    session: AsyncSession, name: str, scope: TokenScope = TokenScope.FULL
) -> tuple[ApiToken, str]:
    """Returns the saved row and the token itself, which can't be read back later."""
    token = TOKEN_PREFIX + secrets.token_urlsafe(32)
    row = ApiToken(name=name, token_hash=_hash_token(token), scope=scope)
    session.add(row)
    try:
        await session.commit()
    except IntegrityError as error:
        await session.rollback()
        raise DuplicateTokenNameError(f'A token named "{name}" already exists') from error
    return row, token


async def token_scope(session: AsyncSession, token: str) -> TokenScope | None:
    """The token's scope, or None when it isn't a valid token."""
    result = await session.execute(
        select(ApiToken).where(ApiToken.token_hash == _hash_token(token))
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    await _note_use(session, row, utcnow())
    return TokenScope(row.scope)


async def _note_use(session: AsyncSession, row: ApiToken, now: datetime) -> None:
    last_used = row.last_used_at
    if last_used is not None and now - last_used.replace(tzinfo=now.tzinfo) < LAST_USED_PRECISION:
        return
    row.last_used_at = now
    await session.commit()
