import asyncio
from urllib.parse import urlparse

from fastapi import APIRouter, WebSocket

from yt_dlp_z.api.deps import is_authenticated
from yt_dlp_z.api.state import AppState
from yt_dlp_z.services.events import Event

router = APIRouter()

UNAUTHORIZED_CLOSE_CODE = 4401


def _same_origin(websocket: WebSocket) -> bool:
    """Blocks cross-site WebSocket hijacking: browsers always send Origin."""
    origin = websocket.headers.get("origin")
    if origin is None:
        return True
    return urlparse(origin).netloc == websocket.headers.get("host")


async def _forward_events(websocket: WebSocket, queue: asyncio.Queue[Event]) -> None:
    while True:
        await websocket.send_json(await queue.get())


async def _wait_for_disconnect(websocket: WebSocket) -> None:
    while (await websocket.receive())["type"] != "websocket.disconnect":
        pass


@router.websocket("/api/ws")
async def events(websocket: WebSocket) -> None:
    state: AppState = websocket.app.state.app_state
    async with state.session_factory() as db:
        allowed = _same_origin(websocket) and await is_authenticated(websocket, state, db)
    if not allowed:
        await websocket.close(code=UNAUTHORIZED_CLOSE_CODE)
        return

    await websocket.accept()
    queue = state.hub.subscribe()
    tasks = {
        asyncio.create_task(_forward_events(websocket, queue)),
        asyncio.create_task(_wait_for_disconnect(websocket)),
    }
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        state.hub.unsubscribe(queue)
