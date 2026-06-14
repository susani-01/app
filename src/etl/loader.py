from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from src.db.models import (
    ClassificationNode,
    MarketPrice,
    QuantityItem,
    Unit,
    WorkDivision,
)
from src.domain.units import normalize_unit

NodeKey = tuple[str, int, str]
ParentKey = tuple[str, int, str]


@dataclass
class EtlStats:
    work_divisions: int = 0
    units: int = 0
    classification_nodes: int = 0
    quantity_items: int = 0
    market_prices: int = 0
    skipped_price_rows: int = 0
    unmapped_units: set[str] = field(default_factory=set)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            records.append(json.loads(line))
    return records


def parse_published_date(value: str | None) -> date | None:
    if not value:
        return None
    cleaned = value.strip()
    if len(cleaned) != 8 or not cleaned.isdigit():
        return None
    return date(int(cleaned[0:4]), int(cleaned[4:6]), int(cleaned[6:8]))


def parse_decimal(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    return Decimal(str(value))


def get_or_create_unit(session: Session, raw_unit: str | None, cache: dict[str, int]) -> int | None:
    canonical = normalize_unit(raw_unit)
    if canonical is None:
        return None

    if canonical in cache:
        return cache[canonical]

    unit = session.scalar(select(Unit).where(Unit.code == canonical))
    if unit is None:
        unit = Unit(code=canonical)
        session.add(unit)
        session.flush()

    cache[canonical] = unit.id
    return unit.id


def extract_level_fields(record: dict[str, Any], level: int) -> tuple[str, str, str]:
    code = str(record.get(f"LvlqtyCalcCtyclCd{level}", "")).strip()
    name = str(record.get(f"LvlqtyCalcCtyclNm{level}", "")).strip()
    description = str(record.get(f"LvlqtyCalcCtyclDscrpt{level}", "")).strip()
    return code, name, description


def deepest_level_codes(record: dict[str, Any]) -> tuple[int, dict[int, str]]:
    codes: dict[int, str] = {}
    deepest = 0
    for level in range(1, 6):
        code, _, _ = extract_level_fields(record, level)
        if code:
            codes[level] = code
            deepest = level
    return deepest, codes


def run_etl(
    session: Session,
    classification_file: Path,
    price_file: Path,
) -> EtlStats:
    stats = EtlStats()
    unit_cache: dict[str, int] = {}

    session.execute(delete(MarketPrice))
    session.execute(delete(QuantityItem))
    session.execute(delete(ClassificationNode))
    session.execute(delete(WorkDivision))
    session.execute(delete(Unit))
    session.flush()

    classification_records = load_jsonl(classification_file)
    price_records = load_jsonl(price_file)

    division_names: dict[str, str] = {}
    for record in classification_records:
        code = str(record.get("cnstwkDivCd", "")).strip()
        name = str(record.get("cnstwkDivNm", "")).strip()
        if code and name:
            division_names[code] = name

    for code, name in sorted(division_names.items()):
        session.add(WorkDivision(code=code, name=name))
    session.flush()
    stats.work_divisions = len(division_names)

    node_payload: dict[NodeKey, dict[str, Any]] = {}
    for record in classification_records:
        division = str(record.get("cnstwkDivCd", "")).strip()
        if not division:
            continue

        parent_key: ParentKey | None = None
        for level in range(1, 6):
            code, name, description = extract_level_fields(record, level)
            if not code:
                break

            key: NodeKey = (division, level, code)
            if key not in node_payload:
                node_payload[key] = {
                    "work_division_cd": division,
                    "level": level,
                    "code": code,
                    "name": name or code,
                    "description": description or None,
                    "parent_key": parent_key,
                }
            parent_key = key

    node_ids: dict[NodeKey, int] = {}
    for level in range(1, 6):
        level_nodes = [
            payload for payload in node_payload.values() if payload["level"] == level
        ]
        for payload in sorted(
            level_nodes,
            key=lambda item: (item["work_division_cd"], item["code"]),
        ):
            parent_id = None
            parent_key = payload["parent_key"]
            if parent_key is not None:
                parent_id = node_ids.get(parent_key)

            node = ClassificationNode(
                work_division_cd=payload["work_division_cd"],
                level=payload["level"],
                code=payload["code"],
                name=payload["name"],
                description=payload["description"],
                parent_id=parent_id,
            )
            session.add(node)
            session.flush()
            node_ids[(payload["work_division_cd"], payload["level"], payload["code"])] = node.id

    stats.classification_nodes = len(node_ids)

    for record in classification_records:
        item_code = str(record.get("qtyCalcCtyclcd", "")).strip()
        if not item_code:
            continue

        division = str(record.get("cnstwkDivCd", "")).strip()
        deepest_level, level_codes = deepest_level_codes(record)
        leaf_node_id = None
        if deepest_level:
            leaf_node_id = node_ids.get((division, deepest_level, level_codes[deepest_level]))

        raw_unit = str(record.get("unit", "")).strip() or None
        canonical = normalize_unit(raw_unit)
        if raw_unit and canonical == raw_unit.strip() and raw_unit not in {
            key for key in unit_cache
        }:
            stats.unmapped_units.add(raw_unit)

        item = QuantityItem(
            qty_calc_ctycl_cd=item_code,
            work_division_cd=division,
            name=str(record.get("qtyCalcCtyclNm", "")).strip() or item_code,
            spec=str(record.get("spec", "")).strip() or None,
            unit_id=get_or_create_unit(session, raw_unit, unit_cache),
            raw_unit=raw_unit,
            leaf_node_id=leaf_node_id,
            lvl1_code=level_codes.get(1),
            lvl2_code=level_codes.get(2),
            lvl3_code=level_codes.get(3),
            lvl4_code=level_codes.get(4),
            lvl5_code=level_codes.get(5),
        )
        session.add(item)

    session.flush()
    stats.quantity_items = session.scalar(select(func.count()).select_from(QuantityItem)) or 0

    item_codes = set(session.scalars(select(QuantityItem.qty_calc_ctycl_cd)).all())
    for record in price_records:
        item_code = str(record.get("qtyCalcCtyclcd", "")).strip()
        if not item_code:
            stats.skipped_price_rows += 1
            continue
        if item_code not in item_codes:
            stats.skipped_price_rows += 1
            continue

        raw_unit = str(record.get("unit", "")).strip() or None
        price = MarketPrice(
            qty_calc_ctycl_cd=item_code,
            product_name=str(record.get("prdnm", "")).strip() or None,
            spec=str(record.get("spec", "")).strip() or None,
            unit_id=get_or_create_unit(session, raw_unit, unit_cache),
            raw_unit=raw_unit,
            material_cost=parse_decimal(record.get("mtrlcstUprc")),
            labor_cost=parse_decimal(record.get("lbrcstUprc")),
            expense_cost=parse_decimal(record.get("gnrexpnsUprc")),
            published_date=parse_published_date(record.get("pblctDate")),
            apply_condition=str(record.get("uprcAplCndtnCntnts", "")).strip() or None,
        )
        session.add(price)

    session.flush()
    stats.market_prices = session.scalar(select(func.count()).select_from(MarketPrice)) or 0
    stats.units = session.scalar(select(func.count()).select_from(Unit)) or 0
    session.commit()
    return stats
