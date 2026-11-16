"""Tests for SHA-256 content-based duplicate detection."""

from app.duplicate_detector import (
    duplicate_summary,
    find_duplicates,
    group_by_size,
    hash_file,
)
from app.scanner import scan_directory


def _find(tmp_path):
    return find_duplicates(scan_directory(tmp_path).files)


def test_same_content_different_names_are_duplicates(tmp_path):
    (tmp_path / "notes.txt").write_text("identical content")
    (tmp_path / "copy_of_notes.txt").write_text("identical content")

    groups = _find(tmp_path)
    assert len(groups) == 1
    assert {f.name for f in groups[0].files} == {"notes.txt", "copy_of_notes.txt"}


def test_same_name_different_content_is_not_a_duplicate(tmp_path):
    (tmp_path / "report.pdf").write_text("version one")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "report.pdf").write_text("version two")

    assert _find(tmp_path) == []


def test_same_size_different_content_is_not_a_duplicate(tmp_path):
    (tmp_path / "a.txt").write_text("aaaaaaaa")
    (tmp_path / "b.txt").write_text("bbbbbbbb")

    assert len(_find(tmp_path)[0:1]) == 0


def test_duplicates_found_across_nested_directories(tmp_path):
    content = "shared content across folders"
    (tmp_path / "one.txt").write_text(content)
    nested = tmp_path / "deep" / "deeper"
    nested.mkdir(parents=True)
    (nested / "two.txt").write_text(content)

    groups = _find(tmp_path)
    assert len(groups) == 1 and groups[0].count == 2


def test_three_copies_form_one_group(tmp_path):
    for name in ("a.txt", "b.txt", "c.txt"):
        (tmp_path / name).write_text("triple")

    groups = _find(tmp_path)
    assert len(groups) == 1
    assert groups[0].count == 3
    assert groups[0].wasted_bytes == len("triple") * 2


def test_summary_numbers(tmp_path):
    (tmp_path / "x1.txt").write_text("1234567890")
    (tmp_path / "x2.txt").write_text("1234567890")
    (tmp_path / "y1.bin").write_text("abcde")
    (tmp_path / "y2.bin").write_text("abcde")
    (tmp_path / "unique.txt").write_text("nothing matches this one")

    stats = duplicate_summary(_find(tmp_path))
    assert stats["group_count"] == 2
    assert stats["duplicate_file_count"] == 4
    assert stats["redundant_file_count"] == 2
    assert stats["recoverable_bytes"] == 10 + 5


def test_empty_files_are_ignored_by_default(tmp_path):
    (tmp_path / "empty1.txt").touch()
    (tmp_path / "empty2.txt").touch()

    assert _find(tmp_path) == []
    files = scan_directory(tmp_path).files
    assert len(find_duplicates(files, ignore_empty_files=False)) == 1


def test_no_duplicates_returns_empty_list(tmp_path):
    (tmp_path / "a.txt").write_text("one")
    (tmp_path / "b.txt").write_text("two different")

    assert _find(tmp_path) == []
    assert duplicate_summary([])["recoverable_bytes"] == 0


def test_group_by_size_buckets_correctly(tmp_path):
    (tmp_path / "a.txt").write_text("1234")
    (tmp_path / "b.txt").write_text("5678")
    (tmp_path / "c.txt").write_text("longer content")

    buckets = group_by_size(scan_directory(tmp_path).files)
    assert len(buckets[4]) == 2
    assert len(buckets[len("longer content")]) == 1


def test_hash_file_is_stable_and_content_dependent(tmp_path):
    first = tmp_path / "a.txt"
    second = tmp_path / "b.txt"
    first.write_text("content")
    second.write_text("content")
    other = tmp_path / "c.txt"
    other.write_text("different")

    digest = hash_file(first)
    assert len(digest) == 64
    assert digest == hash_file(second)
    assert digest != hash_file(other)


def test_hash_file_of_missing_file_returns_none(tmp_path):
    assert hash_file(tmp_path / "does_not_exist.txt") is None


def test_large_file_hashed_in_chunks(tmp_path):
    big = tmp_path / "big1.bin"
    payload = b"x" * (256 * 1024)      # larger than one 64 KB chunk
    big.write_bytes(payload)
    twin = tmp_path / "big2.bin"
    twin.write_bytes(payload)

    groups = _find(tmp_path)
    assert len(groups) == 1 and groups[0].count == 2
