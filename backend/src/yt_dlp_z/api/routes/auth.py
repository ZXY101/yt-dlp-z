from fastapi import APIRouter, HTTPException, Request, Response, status

from yt_dlp_z.api.deps import Db, State, is_authenticated
from yt_dlp_z.api.session_cookie import clear_session_cookie, set_session_cookie
from yt_dlp_z.core.config import AuthMode
from yt_dlp_z.schemas.auth import AuthStatus, LoginRequest, SetupRequest
from yt_dlp_z.services import auth_service
from yt_dlp_z.services.paths import InvalidPathError, prepare_download_dir

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/status")
async def get_status(request: Request, state: State, db: Db) -> AuthStatus:
    return AuthStatus(
        setup_required=not await auth_service.is_setup_complete(db),
        authenticated=await is_authenticated(request, state, db),
        auth_mode=state.settings.auth_mode,
        default_download_dir=str(state.settings.default_download_dir),
    )


@router.post("/setup", status_code=status.HTTP_204_NO_CONTENT)
async def setup(body: SetupRequest, request: Request, state: State, db: Db) -> Response:
    if await auth_service.is_setup_complete(db):
        raise HTTPException(status.HTTP_409_CONFLICT, "Setup is already complete")
    uses_password = state.settings.auth_mode is AuthMode.PASSWORD
    if uses_password and body.password is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "A password is required")
    try:
        download_dir = prepare_download_dir(body.download_dir)
    except InvalidPathError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error

    await auth_service.complete_setup(db, body.password if uses_password else None, download_dir)
    return await _signed_in_response(request, state, db)


@router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
async def login(body: LoginRequest, request: Request, state: State, db: Db) -> Response:
    client_ip = request.client.host if request.client else "unknown"
    retry_after = state.login_limiter.retry_after(client_ip)
    if retry_after:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many failed attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )
    if not await auth_service.check_password(db, body.password):
        state.login_limiter.record_failure(client_ip)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect password")

    state.login_limiter.reset(client_ip)
    return await _signed_in_response(request, state, db)


async def _signed_in_response(request: Request, state: State, db: Db) -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    session_version = await auth_service.get_session_version(db)
    set_session_cookie(response, request, state.signer, session_version)
    return response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    clear_session_cookie(response)
