"""Small JSON cache I/O helpers used by both transcript and summary caches.

Two reasons we centralize this:
- Atomic writes (temp file + os.replace) avoid leaving a half-written cache file
  on disk if the process is killed mid-write.
- Defensive reads return ``None`` for missing / corrupt / non-dict payloads
  instead of crashing the request, since cache corruption is recoverable
  (we just regenerate).
"""

import json
import logging
import tempfile
from pathlib import Path


logger = logging.getLogger(__name__)


def read_json_dict_safe(path: Path) -> dict | None:
    """Read a JSON file expected to contain a dict.

    Returns ``None`` if the file is missing, unreadable, malformed, or not a
    JSON object.
    """
    try:
        text = path.read_text(encoding='utf-8')
    except (OSError, FileNotFoundError):
        return None

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None
    return data


def write_json_atomic(path: Path, data: dict, *, indent: int | None = None) -> None:
    """Write ``data`` to ``path`` atomically (temp file + replace).

    The parent directory is created if missing. On any failure before the
    final ``replace``, the temp file is best-effort removed.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            delete=False,
            dir=str(path.parent),
            prefix=f'{path.stem}.',
            suffix='.tmp',
        ) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(json.dumps(data, ensure_ascii=False, indent=indent))
        tmp_path.replace(path)
    finally:
        if tmp_path and tmp_path.exists() and tmp_path != path:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError as e:
                logger.warning('Failed to remove cache temp file %s: %s', tmp_path, e)
