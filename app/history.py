"""Operation history stored in a plain JSON file.

Every organize run is written as one entry containing each individual move, so
the operation can be reversed later. A JSON file is enough here - no database
is needed for a log this small, and it stays readable for a demonstration.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

DEFAULT_HISTORY_FILE = Path(__file__).resolve().parent.parent / "history.json"


def _read_all(history_file: Path) -> list[dict]:
    """Load the history list, tolerating a missing or corrupted file."""
    if not history_file.exists():
        return []
    try:
        with open(history_file, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _write_all(history_file: Path, entries: list[dict]) -> None:
    history_file.parent.mkdir(parents=True, exist_ok=True)
    with open(history_file, "w", encoding="utf-8") as handle:
        json.dump(entries, handle, indent=2)


def record_operation(
    root: str,
    moves: list[dict],
    history_file: Path | str = DEFAULT_HISTORY_FILE,
    operation_type: str = "organize",
) -> str:
    """Append one operation to the history and return its id.

    Each move is {"source": original path, "destination": new path, "status": ...}
    """
    history_file = Path(history_file)
    entries = _read_all(history_file)
    operation_id = uuid.uuid4().hex[:12]
    entries.append({
        "operation_id": operation_id,
        "operation_type": operation_type,
        "root": str(root),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "file_count": len(moves),
        "undone": False,
        "moves": moves,
    })
    _write_all(history_file, entries)
    return operation_id


def load_history(history_file: Path | str = DEFAULT_HISTORY_FILE) -> list[dict]:
    """Return all operations, newest first."""
    return list(reversed(_read_all(Path(history_file))))


def last_undoable_operation(
    history_file: Path | str = DEFAULT_HISTORY_FILE,
) -> dict | None:
    """The most recent organize operation that has not been undone yet."""
    for entry in reversed(_read_all(Path(history_file))):
        if entry.get("operation_type") == "organize" and not entry.get("undone"):
            return entry
    return None


def mark_undone(
    operation_id: str,
    history_file: Path | str = DEFAULT_HISTORY_FILE,
) -> None:
    """Flag an operation as reversed so it cannot be undone twice."""
    history_file = Path(history_file)
    entries = _read_all(history_file)
    for entry in entries:
        if entry.get("operation_id") == operation_id:
            entry["undone"] = True
            entry["undone_at"] = datetime.now().isoformat(timespec="seconds")
    _write_all(history_file, entries)


def clear_history(history_file: Path | str = DEFAULT_HISTORY_FILE) -> None:
    """Erase the log. This only removes history records, never any real file."""
    _write_all(Path(history_file), [])
