"""Preview and execution of safe file organisation.

Two clearly separated phases:
  1. build_preview() - pure planning. Reads nothing, writes nothing, touches no
     file. It produces the list of proposed moves the user reviews.
  2. organize()      - executes an already-approved plan with shutil.move.

Safety rules enforced here:
  * no file is ever deleted
  * no existing file is ever overwritten (a unique name is generated instead)
  * files already in their correct category folder are skipped
  * SmartFile's own source files are never moved
"""

from __future__ import annotations

import shutil
from pathlib import Path

from app.history import mark_undone, record_operation
from app.models import OperationResult, OrganizePreview, PlannedMove, ScanResult
from app.utils import (
    CATEGORY_FOLDERS,
    is_app_path,
    is_protected_path,
    safe_unique_path,
)


def build_preview(scan_result: ScanResult) -> OrganizePreview:
    """Plan where every scanned file would go. Nothing is moved.

    Destination conflicts are resolved against the files already on disk *and*
    against earlier moves in this same plan, so two files that would land on
    the same name are both given distinct names.
    """
    root = Path(scan_result.root)
    preview = OrganizePreview(root=str(root))

    if is_protected_path(root):
        preview.warnings.append(
            f"'{root}' looks like a system or home directory. "
            "Organising it is not recommended - choose a specific folder such as Downloads."
        )

    # Names already claimed by this plan, so two sources cannot collide.
    planned_destinations: set[str] = set()

    for record in scan_result.files:
        source = Path(record.path)
        category_folder = root / record.category
        destination = category_folder / source.name

        if is_app_path(source):
            preview.moves.append(PlannedMove(
                source=str(source), destination=str(source), category=record.category,
                size_bytes=record.size_bytes, status="skipped",
                note="Belongs to the SmartFile application",
            ))
            continue

        if source.parent == category_folder:
            preview.moves.append(PlannedMove(
                source=str(source), destination=str(source), category=record.category,
                size_bytes=record.size_bytes, status="skipped",
                note="Already in the correct category folder",
            ))
            continue

        status, note = "ready", ""
        if destination.exists() or str(destination) in planned_destinations:
            destination = _unique_against(destination, planned_destinations)
            status = "renamed"
            note = f"A file named '{source.name}' already exists; will be saved as '{destination.name}'"

        planned_destinations.add(str(destination))
        preview.moves.append(PlannedMove(
            source=str(source), destination=str(destination), category=record.category,
            size_bytes=record.size_bytes, status=status, note=note,
        ))

    if not preview.ready:
        preview.warnings.append("Nothing to organise - every file is already in place.")
    return preview


def _unique_against(destination: Path, claimed: set[str]) -> Path:
    """Find a free name, considering both the disk and names claimed in the plan."""
    candidate = safe_unique_path(destination)
    stem, suffix, parent = destination.stem, destination.suffix, destination.parent
    counter = 1
    while str(candidate) in claimed:
        candidate = parent / f"{stem}_{counter}{suffix}"
        counter += 1
        if not candidate.exists() and str(candidate) not in claimed:
            break
    return candidate


def organize(
    preview: OrganizePreview,
    history_file: Path | str | None = None,
) -> OperationResult:
    """Execute an approved plan and log it so it can be undone."""
    from app.history import DEFAULT_HISTORY_FILE

    history_file = Path(history_file) if history_file else DEFAULT_HISTORY_FILE
    result = OperationResult(skipped=len(preview.skipped))
    completed: list[dict] = []

    for move in preview.ready:
        source, destination = Path(move.source), Path(move.destination)
        try:
            if not source.exists():
                result.failed += 1
                result.errors.append(f"{source.name}: no longer exists")
                continue

            destination.parent.mkdir(parents=True, exist_ok=True)
            # Re-check at execution time: the disk may have changed since the
            # preview was built, and we must never overwrite anything.
            if destination.exists():
                destination = safe_unique_path(destination)

            shutil.move(str(source), str(destination))
            result.moved += 1
            completed.append({
                "source": str(source),
                "destination": str(destination),
                "category": move.category,
                "status": "moved",
            })
        except (OSError, PermissionError, shutil.Error) as error:
            result.failed += 1
            result.errors.append(f"{source.name}: {error}")

    if completed:
        result.operation_id = record_operation(
            root=preview.root, moves=completed, history_file=history_file
        )
    return result


def undo_operation(
    operation: dict,
    history_file: Path | str | None = None,
) -> OperationResult:
    """Move files from an earlier operation back to their original locations.

    If an original path is occupied again, the file is restored under a safe
    unique name rather than overwriting whatever is there now.
    """
    from app.history import DEFAULT_HISTORY_FILE

    history_file = Path(history_file) if history_file else DEFAULT_HISTORY_FILE
    result = OperationResult(operation_id=operation.get("operation_id"))

    if operation.get("undone"):
        result.errors.append("This operation has already been undone.")
        return result

    for move in operation.get("moves", []):
        current = Path(move["destination"])
        original = Path(move["source"])
        try:
            if not current.exists():
                result.failed += 1
                result.errors.append(
                    f"{current.name}: not found at its new location "
                    "(it may have been moved or renamed outside SmartFile)"
                )
                continue

            original.parent.mkdir(parents=True, exist_ok=True)
            target = original if not original.exists() else safe_unique_path(original)
            shutil.move(str(current), str(target))
            result.moved += 1
        except (OSError, PermissionError, shutil.Error) as error:
            result.failed += 1
            result.errors.append(f"{current.name}: {error}")

    if result.moved:
        mark_undone(operation["operation_id"], history_file=history_file)
        _remove_empty_category_folders(Path(operation["root"]))
    return result


def _remove_empty_category_folders(root: Path) -> None:
    """Tidy up category folders left empty by an undo. Only empty dirs go."""
    for folder_name in CATEGORY_FOLDERS:
        folder = root / folder_name
        try:
            if folder.is_dir() and not any(folder.iterdir()):
                folder.rmdir()
        except OSError:
            pass        # a non-empty or locked folder is simply left alone
