"""CSV profiling with transparent, dependency-free quality checks."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from statistics import mean, median
from typing import Any


def _quantile(sorted_values: list[float], fraction: float) -> float:
    """Linear-interpolated quantile, deterministic for small and large samples."""
    if not sorted_values:
        raise ValueError("quantile needs at least one value")
    position = (len(sorted_values) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def _number(value: str) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _detect_delimiter(stream, requested: str | None) -> str:
    if requested is not None:
        if len(requested) != 1:
            raise ValueError("delimiter must be exactly one character")
        return requested
    sample = stream.read(8192)
    stream.seek(0)
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def _column_profile(name: str, values: list[str]) -> dict[str, Any]:
    missing = [value for value in values if not value.strip()]
    present = [value.strip() for value in values if value.strip()]
    numeric = [_number(value) for value in present]
    numeric_values = [value for value in numeric if value is not None]
    is_numeric = bool(present) and len(numeric_values) == len(present)

    result: dict[str, Any] = {
        "name": name,
        "type": "numeric" if is_numeric else "text",
        "row_count": len(values),
        "missing_count": len(missing),
        "missing_percent": round(100 * len(missing) / len(values), 2) if values else 0.0,
        "unique_count": len(set(present)),
    }
    if is_numeric:
        ordered = sorted(numeric_values)
        q1 = _quantile(ordered, 0.25)
        q3 = _quantile(ordered, 0.75)
        spread = q3 - q1
        lower = q1 - 1.5 * spread
        upper = q3 + 1.5 * spread
        result["numeric"] = {
            "count": len(ordered),
            "mean": round(mean(ordered), 6),
            "median": round(median(ordered), 6),
            "min": min(ordered),
            "max": max(ordered),
            "q1": round(q1, 6),
            "q3": round(q3, 6),
            "iqr_outlier_count": sum(value < lower or value > upper for value in ordered),
        }
    return result


def profile_csv(path: str | Path, delimiter: str | None = None) -> dict[str, Any]:
    """Profile a CSV file and return a JSON-serializable quality report.

    Malformed records with a different number of fields are counted and skipped.
    A row is considered missing when a field is empty or whitespace-only.
    """
    source = Path(path)
    with source.open("r", encoding="utf-8-sig", newline="") as stream:
        selected_delimiter = _detect_delimiter(stream, delimiter)
        reader = csv.reader(stream, delimiter=selected_delimiter)
        try:
            header = next(reader)
        except StopIteration as error:
            raise ValueError("CSV file is empty") from error

        columns = [item.strip() for item in header]
        if not columns or any(not item for item in columns):
            raise ValueError("CSV header must contain non-empty column names")
        if len(set(columns)) != len(columns):
            raise ValueError("CSV header contains duplicate column names")

        collected: list[list[str]] = [[] for _ in columns]
        seen_rows: set[tuple[str, ...]] = set()
        row_count = 0
        duplicate_count = 0
        malformed_count = 0

        for row in reader:
            if not row:
                continue
            if len(row) != len(columns):
                malformed_count += 1
                continue
            normalized = tuple(value.strip() for value in row)
            row_count += 1
            if normalized in seen_rows:
                duplicate_count += 1
            else:
                seen_rows.add(normalized)
            for index, value in enumerate(row):
                collected[index].append(value)

    profiles = [_column_profile(name, values) for name, values in zip(columns, collected)]
    total_cells = row_count * len(columns)
    missing_cells = sum(item["missing_count"] for item in profiles)
    return {
        "file": source.name,
        "delimiter": selected_delimiter,
        "row_count": row_count,
        "column_count": len(columns),
        "duplicate_row_count": duplicate_count,
        "malformed_row_count": malformed_count,
        "missing_cell_count": missing_cells,
        "missing_cell_percent": round(100 * missing_cells / total_cells, 2) if total_cells else 0.0,
        "columns": profiles,
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Render a compact, deterministic Markdown report."""
    lines = [
        f"# Dataset quality report: {report['file']}",
        "",
        f"- Rows analysed: **{report['row_count']}**",
        f"- Columns: **{report['column_count']}**",
        f"- Duplicate rows: **{report['duplicate_row_count']}**",
        f"- Malformed rows skipped: **{report['malformed_row_count']}**",
        f"- Missing cells: **{report['missing_cell_count']} ({report['missing_cell_percent']}%)**",
        "",
        "| Column | Type | Missing | Unique | Numeric summary |",
        "|---|---|---:|---:|---|",
    ]
    for column in report["columns"]:
        numeric = column.get("numeric")
        summary = (
            f"mean {numeric['mean']}, range {numeric['min']}–{numeric['max']}, "
            f"IQR outliers {numeric['iqr_outlier_count']}"
            if numeric else "—"
        )
        lines.append(
            f"| {column['name']} | {column['type']} | "
            f"{column['missing_count']} ({column['missing_percent']}%) | "
            f"{column['unique_count']} | {summary} |"
        )
    lines.extend([
        "",
        "> Profiling is descriptive, not a guarantee that a dataset is correct. "
        "IQR outliers are review candidates, not automatic errors.",
        "",
    ])
    return "\n".join(lines)
