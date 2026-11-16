"""Recursive directory scanner.

This module is the closest thing in the project to what an OS shell utility
does: it walks the directory tree and reads each file's metadata from the
file system (the stat() system call), without ever opening file contents.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from app.classifier import classify, get_extension
from app.models import FileRecord, ScanResult
from app.utils import creation_time, human_size

# Folders that are never useful to organise and only slow the scan down.
IGNORED_DIRECTORIES = {
    ".git", "__pycache__", ".venv", "venv", "node_modules",
    ".idea", ".vscode", ".pytest_cache", ".mypy_cache",
}


def build_file_record(file_path: Path, root: Path) -> FileRecord:
    """Read one file's metadata and turn it into a FileRecord."""
    stat_result = file_path.stat()       # stat() system call
    size = stat_result.st_size
    return FileRecord(
        name=file_path.name,
        path=str(file_path),
        relative_path=str(file_path.relative_to(root)),
        extension=get_extension(file_path.name),
        category=classify(file_path.name),
        size_bytes=size,
        size_human=human_size(size),
        modified_time=stat_result.st_mtime,
        created_time=creation_time(stat_result),
        parent_dir=str(file_path.parent),
    )


def scan_directory(
    root_path: str | Path,
    include_hidden: bool = False,
    skip_category_folders: bool = False,
) -> ScanResult:
    """Walk `root_path` recursively and collect metadata for every file.

    One unreadable file or a broken symbolic link must never stop the scan, so
    every file-system call is guarded and failures are recorded in `skipped`.
    """
    root = Path(root_path).expanduser().resolve()
    result = ScanResult(root=str(root))

    if not root.is_dir():
        result.skipped.append({"path": str(root), "reason": "Not a directory"})
        return result

    from app.utils import CATEGORY_FOLDERS

    for current_dir, subdirs, filenames in os.walk(root, topdown=True, onerror=None):
        current = Path(current_dir)
        result.directories_scanned += 1

        # Prune directories in place so os.walk never descends into them.
        subdirs[:] = [
            d for d in subdirs
            if d not in IGNORED_DIRECTORIES
            and (include_hidden or not d.startswith("."))
            and not (skip_category_folders and current == root and d in CATEGORY_FOLDERS)
        ]

        visible_files = [
            f for f in filenames if include_hidden or not f.startswith(".")
        ]
        if not subdirs and not visible_files:
            result.empty_directories.append(str(current))

        for filename in visible_files:
            file_path = current / filename
            try:
                if file_path.is_symlink() and not file_path.exists():
                    result.skipped.append(
                        {"path": str(file_path), "reason": "Broken symbolic link"}
                    )
                    continue
                if not file_path.is_file():
                    continue
                result.files.append(build_file_record(file_path, root))
            except PermissionError:
                result.skipped.append(
                    {"path": str(file_path), "reason": "Permission denied"}
                )
            except (OSError, ValueError) as error:
                result.skipped.append(
                    {"path": str(file_path), "reason": f"Inaccessible: {error}"}
                )

    return result


def to_dataframe(scan_result: ScanResult) -> pd.DataFrame:
    """Convert a ScanResult into a DataFrame for analysis and display."""
    columns = [
        "name", "path", "relative_path", "extension", "category",
        "size_bytes", "size_human", "modified_time", "created_time", "parent_dir",
    ]
    if not scan_result.files:
        return pd.DataFrame(columns=columns)

    frame = pd.DataFrame([f.as_dict() for f in scan_result.files])
    frame["modified"] = pd.to_datetime(frame["modified_time"], unit="s")
    frame["created"] = pd.to_datetime(frame["created_time"], unit="s")
    return frame
