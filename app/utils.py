"""Small helpers shared by the other modules: sizes, timestamps and path safety."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime
from pathlib import Path

# Directories that belong to the operating system or to the user's account root.
# Organising these would break the machine, so SmartFile refuses / warns.
PROTECTED_PREFIXES = (
    "/System", "/Library", "/bin", "/sbin", "/usr", "/etc", "/var",
    "/private", "/dev", "/Applications", "/opt",
    "C:\\Windows", "C:\\Program Files",
)

# Category folder names created by the organizer.
CATEGORY_FOLDERS = (
    "Documents", "Images", "Videos", "Audio",
    "Archives", "Code", "Executables", "Others",
)


def human_size(num_bytes: int) -> str:
    """Convert a byte count into a readable string (e.g. 1536 -> '1.5 KB')."""
    if num_bytes < 0:
        return "0 B"
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(size)} B"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def format_time(epoch_seconds: float) -> str:
    """Format an epoch timestamp for display."""
    try:
        return datetime.fromtimestamp(epoch_seconds).strftime("%Y-%m-%d %H:%M:%S")
    except (OverflowError, OSError, ValueError):
        return "unknown"


def creation_time(stat_result) -> float:
    """Return the creation time where the OS provides it.

    macOS/BSD expose st_birthtime. Linux usually does not, so we fall back to
    st_ctime (inode change time) - this is an OS-level difference worth noting.
    """
    return float(getattr(stat_result, "st_birthtime", stat_result.st_ctime))


def safe_unique_path(destination: Path) -> Path:
    """Return a path that does not exist yet, never overwriting an existing file.

    report.pdf -> report_1.pdf -> report_2.pdf ...
    """
    destination = Path(destination)
    if not destination.exists():
        return destination

    stem, suffix, parent = destination.stem, destination.suffix, destination.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _temp_roots() -> tuple[str, ...]:
    """Temporary directories are safe to work in even though macOS places them
    under /var or /private, which are otherwise protected prefixes."""
    temp_dir = tempfile.gettempdir()
    return (temp_dir, str(Path(temp_dir).resolve()))


def is_protected_path(path: str | Path) -> bool:
    """True if the path is a system directory SmartFile should not reorganise."""
    try:
        resolved = str(Path(path).expanduser().resolve())
    except OSError:
        return True
    if any(resolved.startswith(root) for root in _temp_roots()):
        return False
    if resolved == "/" or resolved == str(Path.home()):
        return True
    return any(resolved.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def is_app_path(path: str | Path) -> bool:
    """True if the path belongs to SmartFile's own source tree.

    Prevents the application from moving its own files while it is running.
    `sample_data/` is deliberately excluded - it exists precisely so the
    application can be demonstrated on files inside the project.
    """
    app_root = Path(__file__).resolve().parent.parent
    try:
        relative = Path(path).resolve().relative_to(app_root)
    except (ValueError, OSError):
        return False
    return relative.parts[0] != "sample_data" if relative.parts else False


def validate_directory(path: str | Path) -> tuple[bool, str]:
    """Check a user-supplied directory before doing any work on it."""
    if not str(path).strip():
        return False, "Please enter a directory path."
    target = Path(path).expanduser()
    if not target.exists():
        return False, f"Path does not exist: {target}"
    if not target.is_dir():
        return False, f"Path is not a directory: {target}"
    if not os.access(target, os.R_OK):
        return False, f"No read permission for: {target}"
    return True, "OK"
