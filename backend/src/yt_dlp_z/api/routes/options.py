from fastapi import APIRouter, Depends, HTTPException, status

from yt_dlp_z.api.deps import State, require_auth
from yt_dlp_z.schemas.options import OptionSchema
from yt_dlp_z.services.ytdlp.errors import SchemaUnavailableError

router = APIRouter(prefix="/api/options", tags=["options"], dependencies=[Depends(require_auth)])


@router.get("/schema")
async def get_option_schema(state: State) -> OptionSchema:
    try:
        schema, _ = await state.schemas.get()
    except SchemaUnavailableError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    return schema
