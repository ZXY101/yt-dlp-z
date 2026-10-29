from pydantic import BaseModel, Field

from yt_dlp_z.core.config import AuthMode

MIN_PASSWORD_LENGTH = 8


class AuthStatus(BaseModel):
    setup_required: bool
    authenticated: bool
    auth_mode: AuthMode
    default_download_dir: str


class SetupRequest(BaseModel):
    # Ignored when auth mode is "none".
    password: str | None = Field(default=None, min_length=MIN_PASSWORD_LENGTH, max_length=256)
    download_dir: str = Field(min_length=1, max_length=4096)


class LoginRequest(BaseModel):
    password: str = Field(min_length=1, max_length=256)
