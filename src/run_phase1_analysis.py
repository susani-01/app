"""CLI entry point for Phase 1 exploratory data analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.analysis.analyzer import (
    DEFAULT_CLASSIFICATION_FILE,
    DEFAULT_PRICE_FILE,
    print_summary,
    run_analysis,
)
from src.analysis.report import write_json_report, write_markdown_report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Phase 1 exploratory analysis on construction price datasets.",
    )
    parser.add_argument(
        "--classification-file",
        type=Path,
        default=DEFAULT_CLASSIFICATION_FILE,
        help="Path to construction_classification.jsonl",
    )
    parser.add_argument(
        "--price-file",
        type=Path,
        default=DEFAULT_PRICE_FILE,
        help="Path to std_market_price.jsonl",
    )
    parser.add_argument(
        "--markdown-report",
        type=Path,
        default=Path("docs/reports/phase1_data_analysis.md"),
        help="Path for the generated markdown report",
    )
    parser.add_argument(
        "--json-report",
        type=Path,
        default=Path("docs/reports/phase1_data_analysis.json"),
        help="Path for the generated JSON report",
    )
    args = parser.parse_args()

    report = run_analysis(
        classification_file=args.classification_file,
        price_file=args.price_file,
    )
    print_summary(report)
    write_markdown_report(report, args.markdown_report)
    write_json_report(report, args.json_report)

    print(f"\nMarkdown report written to: {args.markdown_report}")
    print(f"JSON report written to: {args.json_report}")


if __name__ == "__main__":
    main()
