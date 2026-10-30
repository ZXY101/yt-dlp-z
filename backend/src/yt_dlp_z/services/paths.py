import os
from pathlib import Path


class InvalidPathError(ValueError):
    pass


def prepare_download_dir(raw_path: str) -> Path:
    """Validates a user-chosen download folder, creating it if needed."""
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        raise InvalidPathError("Download folder must be an absolute path.")
    path = path.resolve()
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise InvalidPathError(f"Cannot create download folder: {error.strerror}.") from error
    if not os.access(path, os.W_OK):
        raise InvalidPathError("Download folder is not writable.")
    return path


def resolve_job_dir(requested: str | None, base_dir: Path, extra_roots: list[Path]) -> Path:
    """Folder for one download, created if needed. See check_job_dir for the rules."""
    return prepare_download_dir(str(check_job_dir(requested, base_dir, extra_roots)))


def allowed_roots(base_dir: Path, extra_roots: list[Path]) -> list[Path]:
    return [base_dir.resolve(), *(root.resolve() for root in extra_roots)]


def is_inside(path: Path, roots: list[Path]) -> bool:
    return any(path.is_relative_to(root) for root in roots)


def check_job_dir(requested: str | None, base_dir: Path, extra_roots: list[Path]) -> Path:
    """Empty means the default folder, a relative path is inside it, and an absolute
    path must be inside the default folder or an extra root. Creates nothing."""
    raw = (requested or "").strip()
    target = Path(raw).expanduser() if raw else base_dir
    if not target.is_absolute():
        target = base_dir / target
    # resolve() follows symlinks and "..", so the containment check can't be bypassed.
    target = target.resolve()
    roots = allowed_roots(base_dir, extra_roots)
    if not is_inside(target, roots):
        allowed = ", ".join(str(root) for root in roots)
        raise InvalidPathError(f"The folder must be inside: {allowed}.")
    return target
