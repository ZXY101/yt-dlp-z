from fastapi import APIRouter, Depends, HTTPException, status

from yt_dlp_z.api.deps import Db, State, require_auth
from yt_dlp_z.schemas.notifications import NotificationSettingsIn, NotificationSettingsOut
from yt_dlp_z.services.notify.ntfy import NotifyError
from yt_dlp_z.services.notify.store import merge_config, save_config

router = APIRouter(
    prefix="/api/notifications", tags=["notifications"], dependencies=[Depends(require_auth)]
)


@router.get("")
async def get_notifications(state: State) -> NotificationSettingsOut:
    return state.notifier.config.public()


@router.put("")
async def set_notifications(
    body: NotificationSettingsIn, state: State, db: Db
) -> NotificationSettingsOut:
    config = merge_config(state.notifier.config, body)
    await save_config(db, config)
    state.notifier.config = config
    return config.public()


@router.post("/test", status_code=status.HTTP_204_NO_CONTENT)
async def send_test(body: NotificationSettingsIn, state: State) -> None:
    """Sends a test message with these settings, saved or not."""
    config = merge_config(state.notifier.config, body)
    if not config.enabled:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Enter a topic first")
    try:
        await state.notifier.send_test(config)
    except NotifyError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(error)) from error
