"""Shared fixtures. Every test works inside a pytest temporary directory, so
the user's real files are never read, moved or modified."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def sample_tree(tmp_path):
    """A small directory tree covering several categories and a nested folder."""
    (tmp_path / "report.pdf").write_text("a pdf document")
    (tmp_path / "notes.txt").write_text("some notes")
    (tmp_path / "photo.jpg").write_text("image bytes")
    (tmp_path / "song.mp3").write_text("audio bytes")
    (tmp_path / "script.py").write_text("print('hello')")
    (tmp_path / "mystery.xyz").write_text("unknown type")

    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "archive.zip").write_text("archive bytes")
    (nested / "deeper").mkdir()
    (nested / "deeper" / "slides.pptx").write_text("slides")
    return tmp_path


@pytest.fixture
def history_file(tmp_path):
    """An isolated history file so tests never touch the real history.json."""
    return tmp_path / "test_history.json"
