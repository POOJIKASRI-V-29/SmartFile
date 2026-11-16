"""Duplicate detection based on file content, not file names.

Algorithm (two passes, cheap check first):
  1. Group files by size. Files of different sizes can never be identical, and
     size comes free from the metadata the scanner already read.
  2. Only for groups with two or more files of the same size, compute a
     SHA-256 hash by reading the file in fixed-size chunks.
  3. Group by hash; any hash shared by two or more files is a duplicate group.

Reading in chunks keeps memory usage constant, so a 4 GB video is hashed with
the same small buffer as a 4 KB text file.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from app.models import DuplicateGroup, FileRecord

CHUNK_SIZE = 65536      # 64 KB per read - matches typical file-system block reads


def hash_file(file_path: str | Path, chunk_size: int = CHUNK_SIZE) -> str | None:
    """Return the SHA-256 hex digest of a file, or None if it cannot be read."""
    import hashlib

    digest = hashlib.sha256()
    try:
        with open(file_path, "rb") as handle:
            while True:
                chunk = handle.read(chunk_size)
                if not chunk:
                    break
                digest.update(chunk)
    except (OSError, PermissionError):
        return None
    return digest.hexdigest()


def group_by_size(files: list[FileRecord]) -> dict[int, list[FileRecord]]:
    """Step 1: bucket files by their size in bytes."""
    buckets: dict[int, list[FileRecord]] = defaultdict(list)
    for record in files:
        buckets[record.size_bytes].append(record)
    return dict(buckets)


def find_duplicates(
    files: list[FileRecord],
    ignore_empty_files: bool = True,
) -> list[DuplicateGroup]:
    """Return every group of files whose contents are byte-for-byte identical.

    Nothing is ever deleted here - duplicates are only reported.
    """
    groups: list[DuplicateGroup] = []

    for size, candidates in group_by_size(files).items():
        if len(candidates) < 2:
            continue                       # unique size -> cannot be a duplicate
        if ignore_empty_files and size == 0:
            continue                       # every empty file matches every other

        by_hash: dict[str, list[FileRecord]] = defaultdict(list)
        for record in candidates:
            file_hash = hash_file(record.path)
            if file_hash is not None:
                by_hash[file_hash].append(record)

        for file_hash, matched in by_hash.items():
            if len(matched) > 1:
                groups.append(
                    DuplicateGroup(file_hash=file_hash, size_bytes=size, files=matched)
                )

    # Biggest waste first so the user sees the most useful results at the top.
    groups.sort(key=lambda group: group.wasted_bytes, reverse=True)
    return groups


def duplicate_summary(groups: list[DuplicateGroup]) -> dict:
    """Headline numbers for the dashboard."""
    return {
        "group_count": len(groups),
        "duplicate_file_count": sum(group.count for group in groups),
        "redundant_file_count": sum(group.count - 1 for group in groups),
        "recoverable_bytes": sum(group.wasted_bytes for group in groups),
    }
