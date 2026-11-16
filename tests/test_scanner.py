"""Tests for recursive scanning and metadata collection."""

import os
import stat
from pathlib import Path

import pytest

from app.scanner import scan_directory, to_dataframe
from app.utils import human_size


def test_scan_finds_files_recursively(sample_tree):
    result = scan_directory(sample_tree)
    names = {record.name for record in result.files}
    assert names == {
        "report.pdf", "notes.txt", "photo.jpg", "song.mp3",
        "script.py", "mystery.xyz", "archive.zip", "slides.pptx",
    }
    assert result.total_files == 8


def test_scan_collects_metadata(sample_tree):
    result = scan_directory(sample_tree)
    record = next(f for f in result.files if f.name == "report.pdf")

    assert record.extension == ".pdf"
    assert record.category == "Documents"
    assert record.size_bytes == len("a pdf document")
    assert record.size_human == human_size(record.size_bytes)
    assert record.modified_time > 0
    assert record.created_time > 0
    assert Path(record.path).is_absolute()
    assert record.relative_path == "report.pdf"


def test_nested_relative_paths(sample_tree):
    result = scan_directory(sample_tree)
    slides = next(f for f in result.files if f.name == "slides.pptx")
    assert slides.relative_path == str(Path("nested") / "deeper" / "slides.pptx")


def test_empty_directory_returns_no_files(tmp_path):
    result = scan_directory(tmp_path)
    assert result.total_files == 0
    assert result.total_bytes == 0
    assert to_dataframe(result).empty


def test_empty_subdirectories_are_reported(sample_tree):
    (sample_tree / "empty_folder").mkdir()
    result = scan_directory(sample_tree)
    assert any("empty_folder" in d for d in result.empty_directories)


def test_hidden_files_excluded_by_default(sample_tree):
    (sample_tree / ".hidden_file").write_text("secret")
    hidden_dir = sample_tree / ".hidden_dir"
    hidden_dir.mkdir()
    (hidden_dir / "inside.txt").write_text("also hidden")

    default_scan = scan_directory(sample_tree)
    names = {f.name for f in default_scan.files}
    assert ".hidden_file" not in names
    assert "inside.txt" not in names

    with_hidden = scan_directory(sample_tree, include_hidden=True)
    hidden_names = {f.name for f in with_hidden.files}
    assert ".hidden_file" in hidden_names
    assert "inside.txt" in hidden_names


def test_broken_symlink_is_skipped_not_fatal(tmp_path):
    (tmp_path / "real.txt").write_text("content")
    target = tmp_path / "missing.txt"
    link = tmp_path / "broken_link.txt"
    link.symlink_to(target)

    result = scan_directory(tmp_path)
    assert {f.name for f in result.files} == {"real.txt"}
    assert any("Broken symbolic link" in s["reason"] for s in result.skipped)


@pytest.mark.skipif(os.geteuid() == 0, reason="root bypasses permission checks")
def test_unreadable_directory_does_not_crash_scan(tmp_path):
    (tmp_path / "readable.txt").write_text("fine")
    locked = tmp_path / "locked"
    locked.mkdir()
    (locked / "inside.txt").write_text("cannot read")
    os.chmod(locked, 0o000)
    try:
        result = scan_directory(tmp_path)
        assert "readable.txt" in {f.name for f in result.files}
        assert "inside.txt" not in {f.name for f in result.files}
    finally:
        os.chmod(locked, stat.S_IRWXU)


def test_scan_of_non_directory_is_handled(tmp_path):
    a_file = tmp_path / "just_a_file.txt"
    a_file.write_text("x")
    result = scan_directory(a_file)
    assert result.total_files == 0
    assert result.skipped and result.skipped[0]["reason"] == "Not a directory"


def test_dataframe_has_expected_columns(sample_tree):
    frame = to_dataframe(scan_directory(sample_tree))
    for column in ("name", "category", "size_bytes", "modified", "created"):
        assert column in frame.columns
    assert len(frame) == 8
