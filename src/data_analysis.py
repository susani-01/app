"""Backward-compatible wrapper for Phase 1 data analysis."""

from __future__ import annotations

from src.analysis.analyzer import (
    DEFAULT_CLASSIFICATION_FILE,
    DEFAULT_PRICE_FILE,
    print_summary,
    run_analysis,
)

__all__ = [
    "DEFAULT_CLASSIFICATION_FILE",
    "DEFAULT_PRICE_FILE",
    "print_summary",
    "run_analysis",
    "main",
]


def main() -> None:
    report = run_analysis(
        classification_file=DEFAULT_CLASSIFICATION_FILE,
        price_file=DEFAULT_PRICE_FILE,
    )
    print_summary(report)


if __name__ == "__main__":
    main()
