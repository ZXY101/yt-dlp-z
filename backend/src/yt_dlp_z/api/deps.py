from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import HTTPConnection

from yt_dlp_z.api.session_cookie import SESSION_COOKIE
from yt_dlp_z.api.state import AppState
from yt_dlp_z.core.config import AuthMode
from yt_dlp_z.db.models.api_token import TokenScope
from yt_dlp_z.services.api_tokens import token_scope
from yt_dlp_z.services.auth_service import get_session_version


def get_state(request: Request) -> AppState:
    state: AppState = request.app.state.app_state
    return state


State = Annotated[AppState, Depends(get_state)]


async def get_db(state: State) -> AsyncIterator[AsyncSession]:
    async with state.session_factory() as session:
        yield session


Db = Annotated[AsyncSession, Depends(get_db)]

# What a send-only token may call, as (method, route path). Every other route refuses it,
# so a new route stays closed to these tokens until it's added here on purpose.
SEND_SCOPE_ROUTES = frozenset(
    {
        ("GET", "/api/presets"),
        ("POST", "/api/media/probe"),
        ("POST", "/api/jobs/send"),
    }
)


def _bearer_token(connection: HTTPConnection) -> str | None:
    scheme, _, token = connection.headers.get("authorization", "").partition(" ")
    return token.strip() if scheme.lower() == "bearer" else None


async def has_browser_session(
    connection: HTTPConnection, state: AppState, db: AsyncSession
) -> bool:
    if state.settings.auth_mode is AuthMode.NONE:
        return True
    token = connection.cookies.get(SESSION_COOKIE)
    if token is None:
        return False
    token_version = state.signer.read_version(token)
    return token_version is not None and token_version == await get_session_version(db)


async def _bearer_scope(connection: HTTPConnection, db: AsyncSession) -> TokenScope | None:
    token = _bearer_token(connection)
    return None if token is None else await token_scope(db, token)


async def has_api_token(connection: HTTPConnection, state: AppState, db: AsyncSession) -> bool:
    """A token with full access. Send-only tokens don't count."""
    if state.settings.auth_mode is AuthMode.NONE:
        return True
    return await _bearer_scope(connection, db) is TokenScope.FULL


async def is_authenticated(connection: HTTPConnection, state: AppState, db: AsyncSession) -> bool:
    """Full access: a browser session or a full-access token."""
    if await has_browser_session(connection, state, db):
        return True
    return await has_api_token(connection, state, db)


def _route_key(request: Request) -> tuple[str, str | None]:
    route = request.scope.get("route")
    return request.method, getattr(route, "path", None)


async def require_auth(request: Request, state: State, db: Db) -> None:
    if await has_browser_session(request, state, db):
        return
    scope = await _bearer_scope(request, db)
    if scope is TokenScope.FULL:
        return
    if scope is TokenScope.SEND:
        if _route_key(request) in SEND_SCOPE_ROUTES:
            return
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This token can only send links")
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")


async def require_browser_session(request: Request, state: State, db: Db) -> None:
    if not await has_browser_session(request, state, db):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
