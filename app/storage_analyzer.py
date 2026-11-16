"""Storage analytics built on top of a scan result.

Aggregation is done with pandas; the charts are Plotly figures that the
Streamlit UI renders directly.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px

from app.classifier import CATEGORY_ORDER
from app.models import ScanResult
from app.utils import human_size

# Consistent, restrained colours for every chart in the application.
CATEGORY_COLORS = {
    "Documents": "#4C78A8",
    "Images": "#72B7B2",
    "Videos": "#E45756",
    "Audio": "#F58518",
    "Archives": "#9D755D",
    "Code": "#54A24B",
    "Executables": "#B279A2",
    "Others": "#9E9E9E",
}


def overall_stats(scan_result: ScanResult) -> dict:
    """Total files, total storage, average and largest file size."""
    sizes = [f.size_bytes for f in scan_result.files]
    total = sum(sizes)
    count = len(sizes)
    average = total / count if count else 0
    return {
        "total_files": count,
        "total_bytes": total,
        "total_human": human_size(total),
        "average_bytes": average,
        "average_human": human_size(int(average)),
        "largest_bytes": max(sizes) if sizes else 0,
        "largest_human": human_size(max(sizes)) if sizes else "0 B",
        "directories_scanned": scan_result.directories_scanned,
        "skipped_count": len(scan_result.skipped),
    }


def category_breakdown(frame: pd.DataFrame) -> pd.DataFrame:
    """File count and total size per category, largest first."""
    columns = ["category", "file_count", "total_bytes", "total_human", "percent"]
    if frame.empty:
        return pd.DataFrame(columns=columns)

    grouped = (
        frame.groupby("category")
        .agg(file_count=("name", "count"), total_bytes=("size_bytes", "sum"))
        .reset_index()
    )
    grand_total = grouped["total_bytes"].sum()
    grouped["total_human"] = grouped["total_bytes"].apply(human_size)
    grouped["percent"] = (
        grouped["total_bytes"] / grand_total * 100 if grand_total else 0
    ).round(1)
    grouped["order"] = grouped["category"].apply(
        lambda c: CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 99
    )
    return (
        grouped.sort_values(["total_bytes", "order"], ascending=[False, True])
        .drop(columns="order")
        .reset_index(drop=True)[columns]
    )


def largest_files(frame: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    """The `limit` biggest files, ready for display."""
    columns = ["name", "category", "size_human", "relative_path"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    return (
        frame.nlargest(limit, "size_bytes")[columns].reset_index(drop=True)
    )


def extension_breakdown(frame: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    """Most common extensions by file count."""
    columns = ["extension", "file_count", "total_bytes", "total_human"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    grouped = (
        frame.assign(extension=frame["extension"].replace("", "(no extension)"))
        .groupby("extension")
        .agg(file_count=("name", "count"), total_bytes=("size_bytes", "sum"))
        .reset_index()
        .sort_values("file_count", ascending=False)
        .head(limit)
    )
    grouped["total_human"] = grouped["total_bytes"].apply(human_size)
    return grouped.reset_index(drop=True)[columns]


def storage_bar_chart(breakdown: pd.DataFrame):
    """Bar chart: storage used per category."""
    figure = px.bar(
        breakdown, x="category", y="total_bytes", color="category",
        color_discrete_map=CATEGORY_COLORS, text="total_human",
        labels={"total_bytes": "Storage (bytes)", "category": "Category"},
    )
    figure.update_layout(showlegend=False, height=380, margin=dict(t=30, b=10))
    return figure


def count_bar_chart(breakdown: pd.DataFrame):
    """Bar chart: number of files per category."""
    figure = px.bar(
        breakdown, x="category", y="file_count", color="category",
        color_discrete_map=CATEGORY_COLORS, text="file_count",
        labels={"file_count": "Files", "category": "Category"},
    )
    figure.update_layout(showlegend=False, height=380, margin=dict(t=30, b=10))
    return figure


def storage_donut_chart(breakdown: pd.DataFrame):
    """Donut chart: share of total storage per category."""
    figure = px.pie(
        breakdown, names="category", values="total_bytes", hole=0.45,
        color="category", color_discrete_map=CATEGORY_COLORS,
    )
    figure.update_traces(textposition="inside", textinfo="percent+label")
    figure.update_layout(height=380, margin=dict(t=30, b=10))
    return figure
