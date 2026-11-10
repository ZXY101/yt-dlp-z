from fastapi import APIRouter, Depends, HTTPException, status

from yt_dlp_z.api.deps import Db, require_browser_session
from yt_dlp_z.db.models.api_token import ApiToken
from yt_dlp_z.schemas.api_tokens import ApiTokenCreate, ApiTokenCreated, ApiTokenOut
from yt_dlp_z.services import api_tokens

# A token can't manage tokens: an agent holding one must not be able to mint more for
# itself, or outlive being revoked.
router = APIRouter(
    prefix="/api/tokens", tags=["tokens"], dependencies=[Depends(require_browser_session)]
)


@router.get("")
async def list_tokens(db: Db) -> list[ApiTokenOut]:
    return [ApiTokenOut.model_validate(row) for row in await api_tokens.list_tokens(db)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_token(body: ApiTokenCreate, db: Db) -> ApiTokenCreated:
    try:
        row, token = await api_tokens.create_token(db, body.name, body.scope)
    except api_tokens.DuplicateTokenNameError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    return ApiTokenCreated.model_validate(
        {**ApiTokenOut.model_validate(row).__dict__, "token": token}
    )


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_token(token_id: int, db: Db) -> None:
    row = await db.get(ApiToken, token_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Token not found")
    await db.delete(row)
    await db.commit()
