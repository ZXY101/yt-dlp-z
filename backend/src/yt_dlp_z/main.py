import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from yt_dlp_z.api.routes import (
    api_tokens,
    app_settings,
    auth,
    cookies,
    folders,
    health,
    job_actions,
    jobs,
    media,
    notifications,
    options,
    pot,
    presets,
    proxies,
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
from yt_dlp_z.mcp_server.endpoint import mount_mcp
from yt_dlp_z.schemas.ytdlp import YtdlpPreferences
from yt_dlp_z.services.app_settings import (
    get_max_concurrent_downloads,
    get_max_concurrent_recordings,
    get_pot_provider_url,
    get_ytdlp_preferences,
)
from yt_dlp_z.services.auth_service import sync_admin_password
from yt_dlp_z.services.events import EventHub
from yt_dlp_z.services.jobs.context import JobContext
from yt_dlp_z.services.jobs.queues import JobQueues
from yt_dlp_z.services.live.scheduler import LiveScheduler
from yt_dlp_z.services.notify.notifier import Notifier
from yt_dlp_z.services.notify.store import load_config
from yt_dlp_z.services.proxies.pool import ProxyPool
from yt_dlp_z.services.watch.enqueue import WatchContext
from yt_dlp_z.services.watch.retention import RetentionSweeper
from yt_dlp_z.services.watch.watcher import SubscriptionWatcher
from yt_dlp_z.services.ytdlp.pot.provider import PotProvider
from yt_dlp_z.services.ytdlp.schema import OptionSchemaProvider
from yt_dlp_z.services.ytdlp.update_check import UpdateChecker
from yt_dlp_z.services.ytdlp.updater import YtdlpUpdater, ytdlp_python_path
from yt_dlp_z.web import mount_spa

SECONDS_PER_DAY = 86_400


async def _start_services(state: AppState) -> None:
    await state.jobs.start()
    state.live.start()
    state.watcher.start()
    state.update_checker.start()
    await state.pot.start()
    state.retention.start()


async def _stop_services(state: AppState) -> None:
    await state.retention.stop()
    await state.pot.stop()
    await state.update_checker.stop()
    await state.updater.stop()
    await state.watcher.stop()
    await state.live.stop()
    await state.jobs.stop()
    await state.notifier.stop()


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
            notifier = Notifier(await load_config(session))
        hub.listen(notifier.on_event)
        job_context = JobContext(session_factory, hub, settings, schemas, ProxyPool())
        job_queues = JobQueues(job_context, download_limit, recording_limit)
        live = LiveScheduler(job_context, job_queues)
        watcher = SubscriptionWatcher(WatchContext(session_factory, settings, hub, job_queues))
        updater = YtdlpUpdater(
            settings.ytdlp_pip_command, settings.ytdlp_update_dir, schemas.invalidate
        )

        async def ytdlp_preferences() -> YtdlpPreferences:
            async with session_factory() as session:
                return await get_ytdlp_preferences(session)

        update_checker = UpdateChecker(updater, ytdlp_preferences)

        async def pot_provider_url() -> str | None:
            async with session_factory() as session:
                return await get_pot_provider_url(session)

        pot_provider = PotProvider(
            settings.ytdlp_pip_command, settings.plugins_dir, pot_provider_url
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
            update_checker=update_checker,
            notifier=notifier,
            pot=pot_provider,
            retention=RetentionSweeper(job_context),
        )
        if settings.admin_password and settings.auth_mode is AuthMode.PASSWORD:
            async with session_factory() as session:
                await sync_admin_password(session, settings.admin_password.get_secret_value())
        with ytdlp_python_path(settings.ytdlp_update_dir):
            await _start_services(app.state.app_state)
            async with mcp_server.session_manager.run():
                yield
            await _stop_services(app.state.app_state)
        await engine.dispose()

    app = FastAPI(title="yt-dlp-z", lifespan=lifespan)
    app.include_router(health.router)
    for module in (
        api_tokens,
        app_settings,
        auth,
        cookies,
        folders,
        jobs,
        job_actions,
        media,
        notifications,
        options,
        pot,
        presets,
        proxies,
        subscriptions,
        system,
        ws,
        ytdlp,
    ):
        app.include_router(module.router)
    if settings.test_mode:
        app.include_router(testing.router)
    # Before the web app, whose catch-all route would answer /mcp otherwise.
    mcp_server = mount_mcp(app)
    mount_spa(app, settings.frontend_dist)
    return app
