from fastapi import APIRouter, Depends, HTTPException, status

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.schemas.pot import PotProviderIn, PotProviderInfo, PotTestIn, PotTestResult
from yt_dlp_z.services import app_settings
from yt_dlp_z.services.ytdlp.pot.provider import PotProvider
from yt_dlp_z.services.ytdlp.pot.server import PotError, server_version

router = APIRouter(prefix="/api/ytdlp/pot", tags=["ytdlp"], dependencies=[Depends(require_auth)])


def _info(provider: PotProvider) -> PotProviderInfo:
    return PotProviderInfo(
        url=provider.url,
        server_version=provider.server_version,
        error=provider.error,
        checked_at=provider.checked_at,
        plugin_version=provider.plugin_version,
    )


@router.get("")
async def get_pot_provider(state: State) -> PotProviderInfo:
    return _info(state.pot)


@router.put("")
async def set_pot_provider(body: PotProviderIn, state: State, db: Db) -> PotProviderInfo:
    """Checks the server and installs the plugin for its version before saving, so a
    saved provider always works at the time it is saved."""
    try:
        await state.pot.configure(body.url)
    except PotError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(error)) from error
    await app_settings.set_pot_provider_url(db, body.url)
    return _info(state.pot)


@router.post("/test")
async def test_pot_provider(body: PotTestIn) -> PotTestResult:
    try:
        version = await server_version(body.url)
    except PotError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(error)) from error
    return PotTestResult(server_version=version)
