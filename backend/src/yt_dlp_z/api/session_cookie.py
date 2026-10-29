from fastapi import Request, Response

from yt_dlp_z.core.security import SessionSigner

SESSION_COOKIE = "ytdlpz_session"


def set_session_cookie(
    response: Response, request: Request, signer: SessionSigner, session_version: int
) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        signer.sign(session_version),
        max_age=signer.max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, httponly=True, samesite="lax")
