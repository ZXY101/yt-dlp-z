import secrets
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from itsdangerous import BadSignature, URLSafeTimedSerializer

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def load_or_create_secret_key(path: Path) -> str:
    if path.exists():
        return path.read_text().strip()
    path.parent.mkdir(parents=True, exist_ok=True)
    key = secrets.token_urlsafe(48)
    path.write_text(key)
    path.chmod(0o600)
    return key


class SessionSigner:
    """Signs session cookies. The payload carries a session version so that
    changing the password (which bumps the version) logs out every session."""

    def __init__(self, secret_key: str, max_age_seconds: int) -> None:
        self._serializer = URLSafeTimedSerializer(secret_key, salt="session")
        self.max_age_seconds = max_age_seconds

    def sign(self, session_version: int) -> str:
        return self._serializer.dumps({"sv": session_version})

    def read_version(self, token: str) -> int | None:
        try:
            payload = self._serializer.loads(token, max_age=self.max_age_seconds)
        except BadSignature:
            return None
        version = payload.get("sv") if isinstance(payload, dict) else None
        return version if isinstance(version, int) else None
