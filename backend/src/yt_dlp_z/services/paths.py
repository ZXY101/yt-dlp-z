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
