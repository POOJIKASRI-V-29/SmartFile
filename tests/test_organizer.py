"""Tests for preview, safe organisation, conflict handling and undo."""

from pathlib import Path

from app.history import last_undoable_operation, load_history, record_operation
from app.organizer import build_preview, organize, undo_operation
from app.scanner import scan_directory
from app.utils import safe_unique_path


def _preview(path):
    return build_preview(scan_directory(path))


def test_preview_does_not_touch_the_file_system(sample_tree):
    before = sorted(p.name for p in sample_tree.rglob("*"))
    preview = _preview(sample_tree)
    after = sorted(p.name for p in sample_tree.rglob("*"))

    assert before == after
    assert not (sample_tree / "Documents").exists()
    assert len(preview.ready) == 8


def test_preview_proposes_correct_destinations(sample_tree):
    preview = _preview(sample_tree)
    by_source = {Path(m.source).name: m for m in preview.moves}

    assert by_source["report.pdf"].destination == str(sample_tree / "Documents" / "report.pdf")
    assert by_source["photo.jpg"].destination == str(sample_tree / "Images" / "photo.jpg")
    assert by_source["mystery.xyz"].destination == str(sample_tree / "Others" / "mystery.xyz")
    assert by_source["archive.zip"].destination == str(sample_tree / "Archives" / "archive.zip")


def test_preview_counts_per_category(sample_tree):
    counts = _preview(sample_tree).counts_by_category()
    assert counts["Documents"] == 3        # report.pdf, notes.txt, slides.pptx
    assert counts["Images"] == 1
    assert counts["Others"] == 1


def test_organize_moves_files_into_category_folders(sample_tree):
    outcome = organize(_preview(sample_tree), history_file=sample_tree.parent / "h.json")

    assert outcome.moved == 8
    assert outcome.failed == 0
    assert (sample_tree / "Documents" / "report.pdf").exists()
    assert (sample_tree / "Images" / "photo.jpg").exists()
    assert (sample_tree / "Code" / "script.py").exists()
    assert not (sample_tree / "report.pdf").exists()


def test_no_file_is_ever_lost(sample_tree):
    before = sum(1 for p in sample_tree.rglob("*") if p.is_file())
    organize(_preview(sample_tree), history_file=sample_tree.parent / "h.json")
    after = sum(1 for p in sample_tree.rglob("*") if p.is_file())
    assert before == after == 8


def test_name_conflict_gets_a_unique_name_and_keeps_both(tmp_path, history_file):
    (tmp_path / "report.pdf").write_text("first version")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "report.pdf").write_text("second version")

    preview = _preview(tmp_path)
    assert len(preview.conflicts) == 1

    organize(preview, history_file=history_file)
    documents = tmp_path / "Documents"
    contents = sorted(p.read_text() for p in documents.iterdir())
    assert contents == ["first version", "second version"]
    assert (documents / "report.pdf").exists()
    assert (documents / "report_1.pdf").exists()


def test_existing_destination_file_is_never_overwritten(tmp_path, history_file):
    (tmp_path / "Documents").mkdir()
    (tmp_path / "Documents" / "notes.txt").write_text("existing and important")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "notes.txt").write_text("newly organised")

    organize(_preview(tmp_path), history_file=history_file)

    assert (tmp_path / "Documents" / "notes.txt").read_text() == "existing and important"
    assert (tmp_path / "Documents" / "notes_1.txt").read_text() == "newly organised"


def test_files_already_in_place_are_skipped(tmp_path, history_file):
    (tmp_path / "Documents").mkdir()
    settled = tmp_path / "Documents" / "already.txt"
    settled.write_text("in place")

    preview = _preview(tmp_path)
    assert len(preview.ready) == 0
    assert len(preview.skipped) == 1
    assert "Already in the correct category folder" in preview.skipped[0].note

    outcome = organize(preview, history_file=history_file)
    assert outcome.moved == 0
    assert settled.read_text() == "in place"


def test_safe_unique_path_generates_a_sequence(tmp_path):
    target = tmp_path / "file.txt"
    assert safe_unique_path(target) == target

    target.write_text("one")
    first = safe_unique_path(target)
    assert first.name == "file_1.txt"

    first.write_text("two")
    assert safe_unique_path(target).name == "file_2.txt"


def test_protected_directory_raises_a_warning(tmp_path, monkeypatch):
    import app.organizer as organizer
    monkeypatch.setattr(organizer, "is_protected_path", lambda path: True)
    (tmp_path / "a.txt").write_text("x")

    preview = build_preview(scan_directory(tmp_path))
    assert any("system" in warning for warning in preview.warnings)


def test_organize_logs_the_operation(sample_tree, history_file):
    outcome = organize(_preview(sample_tree), history_file=history_file)
    entries = load_history(history_file)

    assert outcome.operation_id is not None
    assert len(entries) == 1
    assert entries[0]["file_count"] == 8
    assert entries[0]["undone"] is False
    assert all("source" in m and "destination" in m for m in entries[0]["moves"])


def test_undo_restores_every_original_path(sample_tree, history_file):
    original = {p.name: str(p) for p in sample_tree.rglob("*") if p.is_file()}
    organize(_preview(sample_tree), history_file=history_file)

    outcome = undo_operation(last_undoable_operation(history_file), history_file=history_file)

    assert outcome.moved == 8
    assert outcome.failed == 0
    for name, path in original.items():
        assert Path(path).exists(), f"{name} was not restored"


def test_undo_removes_empty_category_folders(sample_tree, history_file):
    organize(_preview(sample_tree), history_file=history_file)
    undo_operation(last_undoable_operation(history_file), history_file=history_file)
    assert not (sample_tree / "Documents").exists()
    assert not (sample_tree / "Images").exists()


def test_undo_cannot_run_twice(sample_tree, history_file):
    organize(_preview(sample_tree), history_file=history_file)
    operation = last_undoable_operation(history_file)
    undo_operation(operation, history_file=history_file)

    assert last_undoable_operation(history_file) is None
    repeat = undo_operation(load_history(history_file)[0], history_file=history_file)
    assert repeat.moved == 0
    assert "already been undone" in repeat.errors[0]


def test_undo_explains_missing_files_instead_of_failing_silently(tmp_path, history_file):
    (tmp_path / "a.txt").write_text("x")
    organize(_preview(tmp_path), history_file=history_file)
    (tmp_path / "Documents" / "a.txt").unlink()     # simulate an outside change

    outcome = undo_operation(last_undoable_operation(history_file), history_file=history_file)
    assert outcome.moved == 0
    assert outcome.failed == 1
    assert "not found at its new location" in outcome.errors[0]


def test_undo_does_not_overwrite_a_recreated_original(tmp_path, history_file):
    (tmp_path / "a.txt").write_text("original")
    organize(_preview(tmp_path), history_file=history_file)
    (tmp_path / "a.txt").write_text("recreated later")    # same path taken again

    undo_operation(last_undoable_operation(history_file), history_file=history_file)

    assert (tmp_path / "a.txt").read_text() == "recreated later"
    assert (tmp_path / "a_1.txt").read_text() == "original"


def test_history_records_survive_multiple_operations(tmp_path, history_file):
    record_operation("/some/root", [{"source": "a", "destination": "b", "status": "moved"}],
                     history_file=history_file)
    record_operation("/other/root", [{"source": "c", "destination": "d", "status": "moved"}],
                     history_file=history_file)

    entries = load_history(history_file)
    assert len(entries) == 2
    assert entries[0]["root"] == "/other/root"      # newest first


def test_missing_history_file_is_handled(tmp_path):
    assert load_history(tmp_path / "never_created.json") == []
    assert last_undoable_operation(tmp_path / "never_created.json") is None
