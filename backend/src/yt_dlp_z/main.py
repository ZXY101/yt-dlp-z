import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from yt_dlp_z.api.routes import auth, health, testing
from yt_dlp_z.api.state import AppState
from yt_dlp_z.core.config import Settings, get_settings
from yt_dlp_z.core.security import SessionSigner, load_or_create_secret_key
from yt_dlp_z.db.engine import create_engine, create_session_factory
from yt_dlp_z.db.migrate import upgrade_to_head
from yt_dlp_z.web import mount_spa

SECONDS_PER_DAY = 86_400


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await asyncio.to_thread(upgrade_to_head, settings.database_path)
        engine = create_engine(settings.database_path)
        secret_key = load_or_create_secret_key(settings.secret_key_path)
        app.state.app_state = AppState(
            settings=settings,
            engine=engine,
            session_factory=create_session_factory(engine),
            signer=SessionSigner(secret_key, settings.session_days * SECONDS_PER_DAY),
        )
        yield
        await engine.dispose()

    app = FastAPI(title="yt-dlp-z", lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(auth.router)
    if settings.test_mode:
        app.include_router(testing.router)
    mount_spa(app, settings.frontend_dist)
    return app
