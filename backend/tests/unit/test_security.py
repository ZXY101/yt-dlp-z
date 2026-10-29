from pathlib import Path

from itsdangerous import URLSafeTimedSerializer

from yt_dlp_z.core.security import (
    SessionSigner,
    hash_password,
    load_or_create_secret_key,
    verify_password,
)


def test_password_hash_round_trip() -> None:
    password_hash = hash_password("hunter2-but-longer")
    assert verify_password(password_hash, "hunter2-but-longer")
    assert not verify_password(password_hash, "wrong")


def test_verify_password_rejects_malformed_hash() -> None:
    assert not verify_password("not-a-hash", "anything")


def test_secret_key_is_created_private_and_reused(tmp_path: Path) -> None:
    key_path = tmp_path / "nested" / "secret.key"
    first = load_or_create_secret_key(key_path)
    assert key_path.stat().st_mode & 0o777 == 0o600
    assert load_or_create_secret_key(key_path) == first


def test_session_signer_round_trip() -> None:
    signer = SessionSigner("secret", max_age_seconds=60)
    assert signer.read_version(signer.sign(3)) == 3


def test_session_signer_rejects_tampered_or_foreign_tokens() -> None:
    signer = SessionSigner("secret", max_age_seconds=60)
    other = SessionSigner("other-secret", max_age_seconds=60)
    assert signer.read_version(signer.sign(1) + "x") is None
    assert signer.read_version(other.sign(1)) is None


def test_session_signer_rejects_expired_tokens() -> None:
    signer = SessionSigner("secret", max_age_seconds=-1)
    assert signer.read_version(signer.sign(1)) is None


def test_session_signer_rejects_unexpected_payloads() -> None:
    signer = SessionSigner("secret", max_age_seconds=60)
    raw = URLSafeTimedSerializer("secret", salt="session")
    assert signer.read_version(raw.dumps(["not", "a", "dict"])) is None
    assert signer.read_version(raw.dumps({"sv": "1"})) is None
