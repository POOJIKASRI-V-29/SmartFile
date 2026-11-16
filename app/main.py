"""SmartFile - Streamlit user interface.

Tabs: Dashboard, Scanner, Organize, Duplicates, Storage Analysis, History.
The UI holds no file-system logic of its own; it calls the modules and keeps
the current scan in st.session_state so tabs share one result.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `streamlit run app/main.py` to import the `app` package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from app.duplicate_detector import duplicate_summary, find_duplicates
from app.history import (
    DEFAULT_HISTORY_FILE,
    clear_history,
    last_undoable_operation,
    load_history,
)
from app.organizer import build_preview, organize, undo_operation
from app.scanner import scan_directory, to_dataframe
from app.storage_analyzer import (
    category_breakdown,
    count_bar_chart,
    extension_breakdown,
    largest_files,
    overall_stats,
    storage_bar_chart,
    storage_donut_chart,
)
from app.utils import format_time, human_size, is_protected_path, validate_directory

SAMPLE_DATA_DIR = Path(__file__).resolve().parent.parent / "sample_data"


def init_state() -> None:
    defaults = {
        "scan_result": None,
        "frame": None,
        "preview": None,
        "duplicates": None,
        "last_message": None,
        "active_section": "Dashboard",
        "pending_scan": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def run_scan(path: str, include_hidden: bool) -> None:
    """Scan a directory and store the result for every tab to use."""
    valid, message = validate_directory(path)
    if not valid:
        st.session_state.last_message = ("error", message)
        return

    with st.spinner(f"Scanning {path} ..."):
        result = scan_directory(path, include_hidden=include_hidden)

    st.session_state.scan_result = result
    st.session_state.frame = to_dataframe(result)
    st.session_state.preview = None
    st.session_state.duplicates = None
    st.session_state.last_message = (
        "success",
        f"Scanned {result.total_files} files in {result.directories_scanned} directories "
        f"({human_size(result.total_bytes)}).",
    )


def use_sample_data() -> None:
    """Button callback: point the input at sample_data and queue a scan.

    Callbacks run before the script re-executes, which is the only safe moment
    to set the value of a widget that already exists.
    """
    st.session_state.target_path = str(SAMPLE_DATA_DIR)
    st.session_state.pending_scan = True


def sidebar() -> None:
    with st.sidebar:
        st.header("SmartFile")
        st.caption("OS-based file management & storage optimization")

        # Navigation lives in session_state so pressing a button inside a
        # section does not send the user back to the first section.
        st.radio("Section", SECTIONS, key="active_section")
        st.divider()

        default_path = str(SAMPLE_DATA_DIR) if SAMPLE_DATA_DIR.exists() else str(Path.home())
        path = st.text_input("Directory to scan", value=default_path, key="target_path")
        include_hidden = st.checkbox("Include hidden files", value=False)

        if path and is_protected_path(path):
            st.warning(
                "This looks like a system or home directory. Scanning is read-only "
                "and safe, but organising it is not recommended."
            )

        if st.button("SCAN", type="primary", width="stretch"):
            run_scan(path, include_hidden)

        if SAMPLE_DATA_DIR.exists():
            st.button(
                "Use sample_data", on_click=use_sample_data, width="stretch"
            )

        if st.session_state.pending_scan:
            st.session_state.pending_scan = False
            run_scan(st.session_state.target_path, include_hidden)

        result = st.session_state.scan_result
        if result:
            st.divider()
            st.caption("Current scan")
            st.text(Path(result.root).name or result.root)
            st.text(f"{result.total_files} files · {human_size(result.total_bytes)}")
            if result.skipped:
                st.caption(f"{len(result.skipped)} item(s) skipped")

        st.divider()
        st.caption("SmartFile never deletes files and never overwrites an existing file.")


def dashboard_tab() -> None:
    st.subheader("Dashboard")
    result = st.session_state.scan_result
    if result is None:
        st.info("Enter a directory in the sidebar and press SCAN to begin.")
        return

    stats = overall_stats(result)
    if st.session_state.duplicates is None:
        st.session_state.duplicates = find_duplicates(result.files)
    dup_stats = duplicate_summary(st.session_state.duplicates)

    columns = st.columns(4)
    columns[0].metric("Files scanned", stats["total_files"])
    columns[1].metric("Total storage", stats["total_human"])
    columns[2].metric("Duplicate files", dup_stats["duplicate_file_count"])
    columns[3].metric("Recoverable space", human_size(dup_stats["recoverable_bytes"]))

    columns = st.columns(4)
    columns[0].metric("Directories scanned", stats["directories_scanned"])
    columns[1].metric("Average file size", stats["average_human"])
    columns[2].metric("Largest file", stats["largest_human"])
    columns[3].metric("Skipped items", stats["skipped_count"])

    breakdown = category_breakdown(st.session_state.frame)
    if not breakdown.empty:
        st.markdown("##### Storage by category")
        st.plotly_chart(storage_donut_chart(breakdown), width="stretch",
                        key="dashboard_donut")
        st.dataframe(
            breakdown.rename(columns={
                "category": "Category", "file_count": "Files",
                "total_human": "Size", "percent": "% of storage",
            }).drop(columns="total_bytes"),
            width="stretch", hide_index=True,
        )


def scanner_tab() -> None:
    st.subheader("Scanner")
    result = st.session_state.scan_result
    if result is None:
        st.info("Run a scan first.")
        return

    frame = st.session_state.frame
    st.caption(f"Root: {result.root}")

    categories = ["All"] + sorted(frame["category"].unique().tolist()) if not frame.empty else ["All"]
    chosen = st.selectbox("Filter by category", categories)
    view = frame if chosen == "All" else frame[frame["category"] == chosen]

    if view.empty:
        st.warning("No files matched.")
    else:
        display = view[["name", "category", "extension", "size_human", "relative_path"]].copy()
        display["modified"] = view["modified_time"].apply(format_time)
        st.dataframe(
            display.rename(columns={
                "name": "File", "category": "Category", "extension": "Extension",
                "size_human": "Size", "relative_path": "Path", "modified": "Modified",
            }),
            width="stretch", hide_index=True, height=420,
        )
        st.caption(f"{len(view)} file(s) shown")

    if result.skipped:
        with st.expander(f"Skipped items ({len(result.skipped)})"):
            st.dataframe(pd.DataFrame(result.skipped), width="stretch", hide_index=True)
    if result.empty_directories:
        with st.expander(f"Empty directories ({len(result.empty_directories)})"):
            st.write(result.empty_directories)


def organize_tab() -> None:
    st.subheader("Organize")
    result = st.session_state.scan_result
    if result is None:
        st.info("Run a scan first.")
        return

    st.write(
        "Files are grouped into category folders inside the scanned directory. "
        "Review the preview below - nothing moves until you confirm."
    )

    if st.button("PREVIEW", type="primary"):
        st.session_state.preview = build_preview(result)

    preview = st.session_state.preview
    if preview is None:
        st.caption("Press PREVIEW to see the proposed changes.")
        return

    for warning in preview.warnings:
        st.warning(warning)

    columns = st.columns(4)
    columns[0].metric("Files to move", len(preview.ready))
    columns[1].metric("Name conflicts", len(preview.conflicts))
    columns[2].metric("Skipped", len(preview.skipped))
    columns[3].metric("Categories", len(preview.counts_by_category()))

    counts = preview.counts_by_category()
    if counts:
        st.markdown("##### Files per destination folder")
        st.dataframe(
            pd.DataFrame(sorted(counts.items()), columns=["Destination folder", "Files"]),
            width="stretch", hide_index=True,
        )

    root = Path(preview.root)
    rows = [{
        "Source": _relative(move.source, root),
        "Destination": _relative(move.destination, root),
        "Size": human_size(move.size_bytes),
        "Status": {"ready": "Ready to organize",
                   "renamed": "Renamed to avoid overwrite",
                   "skipped": "Skipped"}[move.status],
        "Note": move.note,
    } for move in preview.moves]
    st.markdown("##### Proposed changes")
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True, height=380)

    if not preview.ready:
        st.info("There is nothing to move.")
        return

    st.divider()
    confirmed = st.checkbox(
        f"I have reviewed the preview and want to move {len(preview.ready)} file(s)."
    )
    if st.button("ORGANIZE", type="primary", disabled=not confirmed):
        with st.spinner("Moving files ..."):
            outcome = organize(preview)
        st.success(f"Moved {outcome.moved} file(s). Skipped {outcome.skipped}.")
        if outcome.errors:
            st.error("Some files could not be moved:")
            for error in outcome.errors:
                st.write(f"- {error}")
        run_scan(preview.root, include_hidden=False)
        st.session_state.preview = None
        st.rerun()


def _relative(path: str, root: Path) -> str:
    try:
        return str(Path(path).relative_to(root))
    except ValueError:
        return path


def duplicates_tab() -> None:
    st.subheader("Duplicates")
    result = st.session_state.scan_result
    if result is None:
        st.info("Run a scan first.")
        return

    st.caption(
        "Files are compared by SHA-256 content hash, not by name. "
        "SmartFile only reports duplicates - it never deletes them."
    )
    if st.button("Find duplicates", type="primary") or st.session_state.duplicates is None:
        with st.spinner("Hashing candidate files ..."):
            st.session_state.duplicates = find_duplicates(result.files)

    groups = st.session_state.duplicates
    stats = duplicate_summary(groups)

    columns = st.columns(4)
    columns[0].metric("Duplicate groups", stats["group_count"])
    columns[1].metric("Duplicate files", stats["duplicate_file_count"])
    columns[2].metric("Redundant copies", stats["redundant_file_count"])
    columns[3].metric("Recoverable space", human_size(stats["recoverable_bytes"]))

    if not groups:
        st.success("No duplicate files found.")
        return

    for index, group in enumerate(groups, start=1):
        with st.expander(
            f"Group {index} - {group.count} identical files, "
            f"{human_size(group.size_bytes)} each, "
            f"{human_size(group.wasted_bytes)} recoverable"
        ):
            st.code(group.file_hash, language=None)
            st.dataframe(
                pd.DataFrame([{
                    "File": f.name, "Size": f.size_human, "Path": f.path,
                } for f in group.files]),
                width="stretch", hide_index=True,
            )


def storage_tab() -> None:
    st.subheader("Storage Analysis")
    result = st.session_state.scan_result
    if result is None:
        st.info("Run a scan first.")
        return

    frame = st.session_state.frame
    breakdown = category_breakdown(frame)
    if breakdown.empty:
        st.warning("No files to analyse.")
        return

    stats = overall_stats(result)
    columns = st.columns(3)
    columns[0].metric("Total storage", stats["total_human"])
    columns[1].metric("Average file size", stats["average_human"])
    columns[2].metric("Largest file", stats["largest_human"])

    left, right = st.columns(2)
    with left:
        st.markdown("##### Storage by category")
        st.plotly_chart(storage_bar_chart(breakdown), width="stretch",
                        key="storage_size_bar")
    with right:
        st.markdown("##### File count by category")
        st.plotly_chart(count_bar_chart(breakdown), width="stretch",
                        key="storage_count_bar")

    st.markdown("##### Storage distribution")
    st.plotly_chart(storage_donut_chart(breakdown), width="stretch",
                    key="storage_donut")

    left, right = st.columns(2)
    with left:
        st.markdown("##### Largest files")
        st.dataframe(
            largest_files(frame, 10).rename(columns={
                "name": "File", "category": "Category",
                "size_human": "Size", "relative_path": "Path",
            }),
            width="stretch", hide_index=True,
        )
    with right:
        st.markdown("##### Most common extensions")
        st.dataframe(
            extension_breakdown(frame, 10).rename(columns={
                "extension": "Extension", "file_count": "Files", "total_human": "Size",
            }).drop(columns="total_bytes"),
            width="stretch", hide_index=True,
        )


def history_tab() -> None:
    st.subheader("History")
    entries = load_history()

    undoable = last_undoable_operation()
    if undoable:
        st.info(
            f"Last operation: {undoable['file_count']} file(s) organised in "
            f"{undoable['root']} at {undoable['timestamp']}."
        )
        if st.button("Undo Last Operation", type="primary"):
            with st.spinner("Restoring files ..."):
                outcome = undo_operation(undoable)
            if outcome.moved:
                st.success(f"Restored {outcome.moved} file(s) to their original locations.")
            if outcome.failed:
                st.error(f"{outcome.failed} file(s) could not be restored:")
                for error in outcome.errors:
                    st.write(f"- {error}")
            if not outcome.moved and not outcome.failed and outcome.errors:
                st.warning(outcome.errors[0])
            if st.session_state.scan_result:
                run_scan(st.session_state.scan_result.root, include_hidden=False)
            st.rerun()
    else:
        st.caption("No operation is available to undo.")

    if not entries:
        st.write("No operations recorded yet.")
        return

    st.markdown("##### Recorded operations")
    st.dataframe(
        pd.DataFrame([{
            "When": entry["timestamp"], "Type": entry["operation_type"],
            "Files": entry["file_count"], "Directory": entry["root"],
            "Undone": "Yes" if entry.get("undone") else "No",
        } for entry in entries]),
        width="stretch", hide_index=True,
    )

    for entry in entries[:5]:
        with st.expander(f"{entry['timestamp']} - {entry['file_count']} file(s)"):
            st.dataframe(
                pd.DataFrame([{
                    "Original path": move["source"],
                    "New path": move["destination"],
                    "Status": move["status"],
                } for move in entry["moves"]]),
                width="stretch", hide_index=True,
            )

    with st.expander("Clear history log"):
        st.caption(
            "This only erases the log file "
            f"({DEFAULT_HISTORY_FILE.name}). No real file is affected, but "
            "cleared operations can no longer be undone."
        )
        if st.button("Clear history"):
            clear_history()
            st.rerun()


SECTIONS = [
    "Dashboard", "Scanner", "Organize", "Duplicates", "Storage Analysis", "History",
]

SECTION_RENDERERS = {
    "Dashboard": dashboard_tab,
    "Scanner": scanner_tab,
    "Organize": organize_tab,
    "Duplicates": duplicates_tab,
    "Storage Analysis": storage_tab,
    "History": history_tab,
}


def main() -> None:
    st.set_page_config(page_title="SmartFile", page_icon="📁", layout="wide")
    init_state()
    sidebar()

    st.title("SmartFile")
    st.caption("OS-Based File Management & Storage Optimization System")

    if st.session_state.last_message:
        level, text = st.session_state.last_message
        getattr(st, level)(text)
        st.session_state.last_message = None

    SECTION_RENDERERS[st.session_state.active_section]()


if __name__ == "__main__":
    main()
