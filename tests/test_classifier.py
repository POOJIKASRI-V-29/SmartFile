"""Tests for extension-based classification."""

import pytest

from app.classifier import (
    CATEGORY_EXTENSIONS,
    all_categories,
    classify,
    classify_extension,
    get_extension,
)


@pytest.mark.parametrize("filename,expected", [
    ("report.pdf", "Documents"),
    ("sheet.xlsx", "Documents"),
    ("photo.jpg", "Images"),
    ("logo.svg", "Images"),
    ("movie.mkv", "Videos"),
    ("track.flac", "Audio"),
    ("backup.zip", "Archives"),
    ("main.cpp", "Code"),
    ("app.dmg", "Executables"),
])
def test_known_extensions(filename, expected):
    assert classify(filename) == expected


def test_classification_is_case_insensitive():
    assert classify("PHOTO.JPG") == "Images"
    assert classify("Report.PDF") == "Documents"
    assert classify_extension(".PNG") == "Images"


def test_unknown_extension_becomes_others():
    assert classify("mystery.xyz") == "Others"
    assert classify("data.qqq") == "Others"


def test_file_without_extension_becomes_others():
    assert classify("README") == "Others"
    assert get_extension("README") == ""


def test_dotfile_is_treated_as_having_no_extension():
    assert get_extension(".gitignore") == ""
    assert classify(".gitignore") == "Others"


def test_multiple_dots_uses_last_extension():
    assert get_extension("archive.tar.gz") == ".gz"
    assert classify("archive.tar.gz") == "Archives"
    assert classify("my.notes.backup.txt") == "Documents"


def test_classify_accepts_full_paths():
    assert classify("/home/user/files/photo.png") == "Images"


def test_classify_extension_without_leading_dot():
    assert classify_extension("mp3") == "Audio"
    assert classify_extension("") == "Others"


def test_no_extension_belongs_to_two_categories():
    seen = set()
    for extensions in CATEGORY_EXTENSIONS.values():
        overlap = seen & set(extensions)
        assert not overlap, f"extension in more than one category: {overlap}"
        seen |= set(extensions)


def test_all_categories_includes_others():
    categories = all_categories()
    assert "Others" in categories
    assert categories[0] == "Documents"
