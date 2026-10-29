from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from platformdirs import user_data_dir, user_downloads_dir
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_DIR = Path(__file__).resolve().parent.parent
REPO_FRONTEND_DIST = PACKAGE_DIR.parents[2] / "frontend" / "dist"


class AuthMode(StrEnum):
    PASSWORD = "password"  # noqa: S105  (an auth mode name, not a secret)
    # Only safe behind a reverse proxy that handles login.
    NONE = "none"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="YTDLPZ_")

    host: str = "127.0.0.1"
    port: int = 9742
    config_dir: Path = Path(user_data_dir("yt-dlp-z", appauthor=False))
    # Pre-filled suggestion in first-run setup; the user picks the real folder there.
    default_download_dir: Path = Path(user_downloads_dir()) / "yt-dlp-z"
    frontend_dist: Path = REPO_FRONTEND_DIST
    auth_mode: AuthMode = AuthMode.PASSWORD
    # When set, this is the admin password and setup asks for it instead of creating one.
    # It is re-applied at every start, so changing it rotates the password.
    admin_password: SecretStr | None = None
    session_days: int = 30
    # Enables /api/test/* endpoints used by the E2E suite. Never set in production.
    test_mode: bool = False

    @property
    def database_path(self) -> Path:
        return self.config_dir / "yt-dlp-z.db"

    @property
    def secret_key_path(self) -> Path:
        return self.config_dir / "secret.key"


@lru_cache
def get_settings() -> Settings:
    return Settings()
