from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_CLASSIFICATION_FILE = Path("data/construction_classification.jsonl")
DEFAULT_PRICE_FILE = Path("data/std_market_price.jsonl")

from src.domain.units import UNIT_NORMALIZATION_MAP, normalize_unit


@dataclass
class AnalysisReport:
    """Structured output from Phase 1 data exploration."""

    classification_file: str
    price_file: str
    classification_rows: int = 0
    price_rows: int = 0
    classification_empty_codes: int = 0
    price_empty_codes: int = 0
    hierarchy_only_rows: int = 0
    leaf_item_rows: int = 0
    unique_classification_codes: int = 0
    unique_price_codes: int = 0
    codes_with_price: int = 0
    codes_without_price: int = 0
    codes_only_in_price: int = 0
    duplicate_classification_codes: int = 0
    duplicate_price_codes: int = 0
    all_zero_price_rows: int = 0
    work_division_counts: dict[str, int] = field(default_factory=dict)
    work_division_names: dict[str, str] = field(default_factory=dict)
    classification_unit_variants: dict[str, int] = field(default_factory=dict)
    price_unit_variants: dict[str, int] = field(default_factory=dict)
    unmapped_units: list[str] = field(default_factory=list)
    unique_hierarchy_paths_by_level: dict[int, int] = field(default_factory=dict)
    published_dates: dict[str, int] = field(default_factory=dict)
    sample_hierarchy_only_row: dict[str, Any] | None = None
    sample_item_without_price: dict[str, Any] | None = None
    sample_item_with_price: dict[str, Any] | None = None
    data_quality_issues: list[str] = field(default_factory=list)
    design_implications: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification_file": self.classification_file,
            "price_file": self.price_file,
            "classification_rows": self.classification_rows,
            "price_rows": self.price_rows,
            "classification_empty_codes": self.classification_empty_codes,
            "price_empty_codes": self.price_empty_codes,
            "hierarchy_only_rows": self.hierarchy_only_rows,
            "leaf_item_rows": self.leaf_item_rows,
            "unique_classification_codes": self.unique_classification_codes,
            "unique_price_codes": self.unique_price_codes,
            "codes_with_price": self.codes_with_price,
            "codes_without_price": self.codes_without_price,
            "codes_only_in_price": self.codes_only_in_price,
            "duplicate_classification_codes": self.duplicate_classification_codes,
            "duplicate_price_codes": self.duplicate_price_codes,
            "all_zero_price_rows": self.all_zero_price_rows,
            "work_division_counts": self.work_division_counts,
            "work_division_names": self.work_division_names,
            "classification_unit_variants": self.classification_unit_variants,
            "price_unit_variants": self.price_unit_variants,
            "unmapped_units": self.unmapped_units,
            "unique_hierarchy_paths_by_level": self.unique_hierarchy_paths_by_level,
            "published_dates": self.published_dates,
            "sample_hierarchy_only_row": self.sample_hierarchy_only_row,
            "sample_item_without_price": self.sample_item_without_price,
            "sample_item_with_price": self.sample_item_with_price,
            "data_quality_issues": self.data_quality_issues,
            "design_implications": self.design_implications,
        }


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            records.append(json.loads(line))
    return records


def _normalize_unit(raw_unit: str) -> str | None:
    return normalize_unit(raw_unit)


def run_analysis(
    classification_file: Path = DEFAULT_CLASSIFICATION_FILE,
    price_file: Path = DEFAULT_PRICE_FILE,
) -> AnalysisReport:
    """Run Phase 1 exploratory analysis on both JSONL datasets."""
    classification_records = _load_jsonl(classification_file)
    price_records = _load_jsonl(price_file)

    report = AnalysisReport(
        classification_file=str(classification_file),
        price_file=str(price_file),
        classification_rows=len(classification_records),
        price_rows=len(price_records),
    )

    classification_codes: Counter[str] = Counter()
    price_codes: Counter[str] = Counter()
    hierarchy_paths: dict[int, set[tuple[str, ...]]] = defaultdict(set)
    seen_units: set[str] = set()

    for record in classification_records:
        code = str(record.get("qtyCalcCtyclcd", "")).strip()
        unit = str(record.get("unit", "")).strip()
        division_code = str(record.get("cnstwkDivCd", "")).strip()
        division_name = str(record.get("cnstwkDivNm", "")).strip()

        if division_code:
            report.work_division_counts[division_code] = (
                report.work_division_counts.get(division_code, 0) + 1
            )
            if division_name:
                report.work_division_names[division_code] = division_name

        if unit:
            report.classification_unit_variants[unit] = (
                report.classification_unit_variants.get(unit, 0) + 1
            )
            seen_units.add(unit)

        if not code:
            report.classification_empty_codes += 1
            report.hierarchy_only_rows += 1
            if report.sample_hierarchy_only_row is None:
                report.sample_hierarchy_only_row = _compact_classification_row(record)
        else:
            report.leaf_item_rows += 1
            classification_codes[code] += 1

        for level in range(1, 6):
            path = tuple(
                str(record.get(f"LvlqtyCalcCtyclCd{index}", "")).strip()
                for index in range(1, level + 1)
            )
            if any(path):
                hierarchy_paths[level].add(path)

    price_code_set: set[str] = set()
    for record in price_records:
        code = str(record.get("qtyCalcCtyclcd", "")).strip()
        unit = str(record.get("unit", "")).strip()
        published_date = str(record.get("pblctDate", "")).strip()

        if not code:
            report.price_empty_codes += 1
        else:
            price_codes[code] += 1
            price_code_set.add(code)

        if unit:
            report.price_unit_variants[unit] = report.price_unit_variants.get(unit, 0) + 1
            seen_units.add(unit)

        if published_date:
            report.published_dates[published_date] = (
                report.published_dates.get(published_date, 0) + 1
            )

        material = float(record.get("mtrlcstUprc") or 0)
        labor = float(record.get("lbrcstUprc") or 0)
        expense = float(record.get("gnrexpnsUprc") or 0)
        if material == 0 and labor == 0 and expense == 0:
            report.all_zero_price_rows += 1

        if report.sample_item_with_price is None and code:
            report.sample_item_with_price = _compact_price_row(record)

    classification_code_set = set(classification_codes)
    report.unique_classification_codes = len(classification_code_set)
    report.unique_price_codes = len(price_code_set)
    report.codes_with_price = len(classification_code_set & price_code_set)
    report.codes_without_price = len(classification_code_set - price_code_set)
    report.codes_only_in_price = len(price_code_set - classification_code_set)
    report.duplicate_classification_codes = sum(
        1 for count in classification_codes.values() if count > 1
    )
    report.duplicate_price_codes = sum(1 for count in price_codes.values() if count > 1)
    report.unique_hierarchy_paths_by_level = {
        level: len(paths) for level, paths in sorted(hierarchy_paths.items())
    }

    for unit in sorted(seen_units):
        if unit not in UNIT_NORMALIZATION_MAP:
            report.unmapped_units.append(unit)

    for record in classification_records:
        code = str(record.get("qtyCalcCtyclcd", "")).strip()
        if code and code not in price_code_set and report.sample_item_without_price is None:
            report.sample_item_without_price = _compact_classification_row(record)

    report.data_quality_issues = _build_data_quality_issues(report)
    report.design_implications = _build_design_implications(report)
    return report


def _compact_classification_row(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "cnstwk_div_cd": record.get("cnstwkDivCd"),
        "cnstwk_div_nm": record.get("cnstwkDivNm"),
        "classification_path": [
            record.get(f"LvlqtyCalcCtyclNm{level}")
            for level in range(1, 6)
            if record.get(f"LvlqtyCalcCtyclNm{level}")
        ],
        "qty_calc_ctycl_cd": record.get("qtyCalcCtyclcd") or None,
        "qty_calc_ctycl_nm": record.get("qtyCalcCtyclNm") or None,
        "spec": record.get("spec"),
        "unit": record.get("unit"),
    }


def _compact_price_row(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "qty_calc_ctycl_cd": record.get("qtyCalcCtyclcd"),
        "product_name": record.get("prdnm"),
        "spec": record.get("spec"),
        "unit": record.get("unit"),
        "material_cost": record.get("mtrlcstUprc"),
        "labor_cost": record.get("lbrcstUprc"),
        "expense_cost": record.get("gnrexpnsUprc"),
        "published_date": record.get("pblctDate"),
    }


def _build_data_quality_issues(report: AnalysisReport) -> list[str]:
    issues: list[str] = []

    if report.hierarchy_only_rows:
        issues.append(
            f"{report.hierarchy_only_rows:,} classification rows have no "
            "`qtyCalcCtyclcd`; they represent hierarchy nodes, not billable items."
        )
    if report.codes_without_price:
        issues.append(
            f"{report.codes_without_price:,} item codes exist in classification "
            "but have no matching price record."
        )
    if report.codes_only_in_price:
        issues.append(
            f"{report.codes_only_in_price:,} price codes are missing from classification."
        )
    if report.duplicate_classification_codes:
        issues.append(
            f"{report.duplicate_classification_codes:,} item codes appear more than once "
            "in classification."
        )
    if report.duplicate_price_codes:
        issues.append(
            f"{report.duplicate_price_codes:,} item codes appear more than once in price data."
        )
    if report.unmapped_units:
        issues.append(
            f"{len(report.unmapped_units)} distinct unit strings are not yet mapped to a "
            "canonical form and need review during ETL."
        )
    if len(report.classification_unit_variants) > 1:
        issues.append(
            "Equivalent units appear under multiple spellings (for example `m`/`M`, "
            "`㎡`/`M2`/`m2`)."
        )

    return issues


def _build_design_implications(report: AnalysisReport) -> list[str]:
    price_coverage_pct = (
        round(report.codes_with_price / report.unique_classification_codes * 100, 1)
        if report.unique_classification_codes
        else 0.0
    )

    return [
        "Treat `construction_classification.jsonl` as the master catalog and "
        "`std_market_price.jsonl` as optional enrichment linked by `qtyCalcCtyclcd`.",
        "Model classification hierarchy nodes separately from leaf-level quantity items.",
        f"Only {price_coverage_pct}% of classified item codes currently have a price; "
        "the API must expose `price: null` explicitly.",
        "Normalize units during ETL before persisting data or serving search/filter results.",
        "Use a left join from items to prices so items without prices remain searchable.",
        "Index item name (`qtyCalcCtyclNm`) and classification filters for the search API.",
    ]


def print_summary(report: AnalysisReport) -> None:
    """Print a human-readable summary to stdout."""
    print("\n=== Phase 1 Data Analysis ===")
    print(f"Classification rows: {report.classification_rows:,}")
    print(f"Price rows: {report.price_rows:,}")
    print(f"Hierarchy-only rows: {report.hierarchy_only_rows:,}")
    print(f"Leaf item rows: {report.leaf_item_rows:,}")
    print(f"Unique item codes (classification): {report.unique_classification_codes:,}")
    print(f"Unique item codes (price): {report.unique_price_codes:,}")
    print(f"Codes with price: {report.codes_with_price:,}")
    print(f"Codes without price: {report.codes_without_price:,}")
    print(f"Codes only in price: {report.codes_only_in_price:,}")

    print("\n=== Work Divisions ===")
    for code, count in sorted(report.work_division_counts.items()):
        name = report.work_division_names.get(code, "")
        print(f"{code} ({name}): {count:,}")

    print("\n=== Data Quality Issues ===")
    for issue in report.data_quality_issues:
        print(f"- {issue}")

    print("\n=== Design Implications ===")
    for implication in report.design_implications:
        print(f"- {implication}")
