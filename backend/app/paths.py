"""Filesystem paths anchored at the backend tree (not the process cwd)."""

from pathlib import Path


def backend_root_dir() -> Path:
    """Directory that contains the ``app`` package (the ``backend`` folder)."""
    return Path(__file__).resolve().parent.parent


def resolve_backend_path(relative_or_absolute: str | Path) -> Path:
    """
    Resolve a configured path for files stored under the backend checkout.

    Absolute paths are returned unchanged. Relative paths are joined to
    ``backend_root_dir()``. A leading ``backend`` segment is stripped so
    ``backend/.cache/x`` and ``.cache/x`` map to the same folder.
    """
    p = Path(relative_or_absolute)
    if p.is_absolute():
        return p

    parts = list(p.parts)
    if parts and parts[0].lower() == 'backend':
        parts = parts[1:]

    return backend_root_dir() / Path(*parts)
