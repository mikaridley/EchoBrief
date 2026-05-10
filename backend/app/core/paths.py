"""Filesystem paths anchored at the backend tree (not the process cwd)."""

from pathlib import Path


_THIS_FILE = Path(__file__).resolve()


def backend_root_dir() -> Path:
    """Directory that contains the ``app`` package (the ``backend`` folder).

    We walk up the filesystem until we find the ``app`` package directory and
    return its parent. This way the lookup keeps working regardless of where
    inside ``app/`` this module physically lives.
    """
    for parent in _THIS_FILE.parents:
        if parent.name == 'app':
            return parent.parent
    raise RuntimeError(f'Could not locate backend root from {_THIS_FILE}')


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
