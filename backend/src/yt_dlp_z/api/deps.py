from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import HTTPConnection

from yt_dlp_z.api.session_cookie import SESSION_COOKIE
from yt_dlp_z.api.state import AppState
from yt_dlp_z.core.config import AuthMode
from yt_dlp_z.services.auth_service import get_session_version


def get_state(request: Request) -> AppState:
    state: AppState = request.app.state.app_state
    return state


State = Annotated[AppState, Depends(get_state)]


async def get_db(state: State) -> AsyncIterator[AsyncSession]:
    async with state.session_factory() as session:
        yield session


Db = Annotated[AsyncSession, Depends(get_db)]


async def is_authenticated(connection: HTTPConnection, state: AppState, db: AsyncSession) -> bool:
    if state.settings.auth_mode is AuthMode.NONE:
        return True
    token = connection.cookies.get(SESSION_COOKIE)
    if token is None:
        return False
    token_version = state.signer.read_version(token)
    return token_version is not None and token_version == await get_session_version(db)


async def require_auth(request: Request, state: State, db: Db) -> None:
    if not await is_authenticated(request, state, db):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
