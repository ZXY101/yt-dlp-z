import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from yt_dlp_z.api.routes import (
    app_settings,
    auth,
    cookies,
    folders,
    health,
    job_actions,
    jobs,
    options,
    presets,
    subscriptions,
    system,
    testing,
    ws,
    ytdlp,
)
from yt_dlp_z.api.state import AppState
from yt_dlp_z.core.config import AuthMode, Settings, get_settings
from yt_dlp_z.core.security import SessionSigner, load_or_create_secret_key
from yt_dlp_z.db.engine import create_engine, create_session_factory
from yt_dlp_z.db.migrate import upgrade_to_head
from yt_dlp_z.services.app_settings import (
    get_max_concurrent_downloads,
    get_max_concurrent_recordings,
)
from yt_dlp_z.services.auth_service import sync_admin_password
from yt_dlp_z.services.events import EventHub
from yt_dlp_z.services.jobs.job_run import JobContext
from yt_dlp_z.services.jobs.queues import JobQueues
from yt_dlp_z.services.live.scheduler import LiveScheduler
from yt_dlp_z.services.watch.enqueue import WatchContext
from yt_dlp_z.services.watch.watcher import SubscriptionWatcher
from yt_dlp_z.services.ytdlp.schema import OptionSchemaProvider
from yt_dlp_z.services.ytdlp.updater import YtdlpUpdater, ytdlp_python_path
from yt_dlp_z.web import mount_spa

SECONDS_PER_DAY = 86_400


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await asyncio.to_thread(upgrade_to_head, settings.database_path)
        engine = create_engine(settings.database_path)
        secret_key = load_or_create_secret_key(settings.secret_key_path)
        session_factory = create_session_factory(engine)
        hub = EventHub()
        schemas = OptionSchemaProvider(allow_unsafe=settings.allow_unsafe_options)
        async with session_factory() as session:
            download_limit = await get_max_concurrent_downloads(
                session, settings.max_concurrent_downloads
            )
            recording_limit = await get_max_concurrent_recordings(
                session, settings.max_concurrent_recordings
            )
        job_context = JobContext(session_factory, hub, settings, schemas)
        job_queues = JobQueues(job_context, download_limit, recording_limit)
        live = LiveScheduler(job_context, job_queues)
        watcher = SubscriptionWatcher(WatchContext(session_factory, settings, hub, job_queues))
        updater = YtdlpUpdater(
            settings.ytdlp_pip_command, settings.ytdlp_update_dir, schemas.invalidate
        )
        app.state.app_state = AppState(
            settings=settings,
            engine=engine,
            session_factory=session_factory,
            signer=SessionSigner(secret_key, settings.session_days * SECONDS_PER_DAY),
            hub=hub,
            schemas=schemas,
            jobs=job_queues,
            live=live,
            watcher=watcher,
            updater=updater,
        )
        if settings.admin_password and settings.auth_mode is AuthMode.PASSWORD:
            async with session_factory() as session:
                await sync_admin_password(session, settings.admin_password.get_secret_value())
        with ytdlp_python_path(settings.ytdlp_update_dir):
            await job_queues.start()
            live.start()
            watcher.start()
            yield
            await updater.stop()
            await watcher.stop()
            await live.stop()
            await job_queues.stop()
        await engine.dispose()

    app = FastAPI(title="yt-dlp-z", lifespan=lifespan)
    app.include_router(health.router)
    for module in (
        app_settings,
        auth,
        cookies,
        folders,
        jobs,
        job_actions,
        options,
        presets,
        subscriptions,
        system,
        ws,
        ytdlp,
    ):
        app.include_router(module.router)
    if settings.test_mode:
        app.include_router(testing.router)
    mount_spa(app, settings.frontend_dist)
    return app
