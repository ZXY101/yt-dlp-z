"""Folder suggestions for the "Save to" field."""

from pathlib import Path

from yt_dlp_z.services.paths import allowed_roots, check_job_dir, is_inside

MAX_SUGGESTIONS = 200


def _child_folders(folder: Path, roots: list[Path]) -> list[str]:
    try:
        children = sorted(folder.iterdir(), key=lambda child: child.name.lower())
    except OSError:
        return []
    names: list[str] = []
    for child in children:
        if child.name.startswith(".") or not child.is_dir():
            continue
        # A symlink pointing outside the allowed folders would be refused later anyway.
        if is_inside(child.resolve(), roots):
            names.append(child.name)
        if len(names) >= MAX_SUGGESTIONS:
            break
    return names


def suggest_folders(parent: str, base_dir: Path, extra_roots: list[Path]) -> list[str]:
    """Sub-folders of `parent`, written the way the user would type them: relative
    to the default folder, or absolute. Raises InvalidPathError outside the roots."""
    folder = check_job_dir(parent, base_dir, extra_roots)
    prefix = parent.strip()
    if prefix and not prefix.endswith("/"):
        prefix += "/"
    names = _child_folders(folder, allowed_roots(base_dir, extra_roots))
    suggestions = [prefix + name for name in names]
    if not prefix:
        suggestions += [str(root) for root in extra_roots]
    return suggestions
