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


def check_job_dir(requested: str | None, base_dir: Path, extra_roots: list[Path]) -> Path:
    """Empty means the default folder, a relative path is inside it, and an absolute
    path must be inside the default folder or an extra root. Creates nothing."""
    raw = (requested or "").strip()
    target = Path(raw).expanduser() if raw else base_dir
    if not target.is_absolute():
        target = base_dir / target
    # resolve() follows symlinks and "..", so the containment check can't be bypassed.
    target = target.resolve()
    roots = [base_dir.resolve(), *(root.resolve() for root in extra_roots)]
    if not any(target.is_relative_to(root) for root in roots):
        allowed = ", ".join(str(root) for root in roots)
        raise InvalidPathError(f"The folder must be inside: {allowed}.")
    return target
