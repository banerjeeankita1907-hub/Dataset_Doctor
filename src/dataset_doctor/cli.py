"""Command-line interface for Dataset Doctor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import profile_csv, render_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dataset-doctor",
        description="Profile a CSV file for missing data, duplicates, malformed rows, and numeric outliers.",
    )
    parser.add_argument("csv_file", type=Path, help="Path to the CSV file")
    parser.add_argument("--delimiter", help="Explicit one-character delimiter (default: detect)")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--output", type=Path, help="Write the report to a file instead of stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = profile_csv(args.csv_file, delimiter=args.delimiter)
        rendered = (
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
            if args.format == "json"
            else render_markdown(report)
        )
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
        return 0
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        print(f"dataset-doctor: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
