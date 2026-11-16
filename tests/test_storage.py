"""Tests for storage aggregation and chart construction."""

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
from app.utils import human_size


def test_overall_stats_totals(tmp_path):
    (tmp_path / "a.txt").write_text("x" * 100)
    (tmp_path / "b.jpg").write_text("y" * 300)

    stats = overall_stats(scan_directory(tmp_path))
    assert stats["total_files"] == 2
    assert stats["total_bytes"] == 400
    assert stats["average_bytes"] == 200
    assert stats["largest_bytes"] == 300
    assert stats["largest_human"] == "300 B"


def test_overall_stats_on_empty_directory(tmp_path):
    stats = overall_stats(scan_directory(tmp_path))
    assert stats["total_files"] == 0
    assert stats["total_bytes"] == 0
    assert stats["average_bytes"] == 0
    assert stats["largest_human"] == "0 B"


def test_category_breakdown_sums_per_category(tmp_path):
    (tmp_path / "a.txt").write_text("x" * 100)
    (tmp_path / "b.txt").write_text("x" * 100)
    (tmp_path / "c.jpg").write_text("y" * 600)

    breakdown = category_breakdown(to_dataframe(scan_directory(tmp_path)))
    by_category = breakdown.set_index("category")

    assert by_category.loc["Documents", "file_count"] == 2
    assert by_category.loc["Documents", "total_bytes"] == 200
    assert by_category.loc["Images", "total_bytes"] == 600
    assert by_category.loc["Images", "percent"] == 75.0
    assert breakdown.iloc[0]["category"] == "Images"        # largest first


def test_category_breakdown_on_empty_frame(tmp_path):
    breakdown = category_breakdown(to_dataframe(scan_directory(tmp_path)))
    assert breakdown.empty
    assert list(breakdown.columns) == [
        "category", "file_count", "total_bytes", "total_human", "percent"
    ]


def test_largest_files_is_sorted_and_limited(tmp_path):
    for index, size in enumerate([50, 500, 5000, 100]):
        (tmp_path / f"file{index}.txt").write_text("x" * size)

    top = largest_files(to_dataframe(scan_directory(tmp_path)), limit=2)
    assert len(top) == 2
    assert top.iloc[0]["name"] == "file2.txt"
    assert top.iloc[1]["name"] == "file1.txt"


def test_extension_breakdown_counts(tmp_path):
    (tmp_path / "a.py").write_text("code")
    (tmp_path / "b.py").write_text("code")
    (tmp_path / "c.txt").write_text("text")
    (tmp_path / "README").write_text("no extension")

    breakdown = extension_breakdown(to_dataframe(scan_directory(tmp_path)))
    counts = dict(zip(breakdown["extension"], breakdown["file_count"]))
    assert counts[".py"] == 2
    assert counts[".txt"] == 1
    assert counts["(no extension)"] == 1


def test_human_size_conversions():
    assert human_size(0) == "0 B"
    assert human_size(512) == "512 B"
    assert human_size(1024) == "1.0 KB"
    assert human_size(1536) == "1.5 KB"
    assert human_size(1024 ** 2) == "1.0 MB"
    assert human_size(1024 ** 3) == "1.0 GB"
    assert human_size(3 * 1024 ** 4) == "3.0 TB"


def test_charts_build_without_error(tmp_path):
    (tmp_path / "a.txt").write_text("x" * 10)
    (tmp_path / "b.jpg").write_text("y" * 20)
    breakdown = category_breakdown(to_dataframe(scan_directory(tmp_path)))

    for figure in (storage_bar_chart(breakdown),
                   count_bar_chart(breakdown),
                   storage_donut_chart(breakdown)):
        assert figure.data            # each chart has at least one trace


def test_total_bytes_matches_sum_of_categories(sample_tree):
    result = scan_directory(sample_tree)
    breakdown = category_breakdown(to_dataframe(result))
    assert breakdown["total_bytes"].sum() == result.total_bytes
    assert breakdown["file_count"].sum() == result.total_files
