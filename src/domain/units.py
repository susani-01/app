"""Unit normalization for ETL."""

from __future__ import annotations

# Known equivalent spellings mapped to a canonical code.
# Unmapped values are stored as trimmed raw strings (preserving source data).
UNIT_NORMALIZATION_MAP: dict[str, str] = {
    "m": "m",
    "M": "m",
    "ｍ": "m",
    "m2": "m2",
    "M2": "m2",
    "㎡": "m2",
    "m3": "m3",
    "M3": "m3",
    "㎥": "m3",
    "공m3": "m3_labor",
    "공M3": "m3_labor",
    "공㎥": "m3_labor",
    "개": "ea",
    "EA": "ea",
    "ea(개)": "ea",
    "개소": "site",
    "nr(개소)": "site",
    "개소당": "site",
    "본": "unit",
    "ton": "ton",
    "TON": "ton",
    "Ton": "ton",
    "톤": "ton",
    "대": "set",
    "SET": "set",
    "식": "lot",
    "km": "km",
    "KM": "km",
    "kg": "kg",
    "hr": "hr",
    "HR": "hr",
}


def normalize_unit(raw_unit: str | None) -> str | None:
    """Return a canonical unit code, or None when the source value is empty."""
    if raw_unit is None:
        return None

    cleaned = raw_unit.strip()
    if not cleaned:
        return None

    return UNIT_NORMALIZATION_MAP.get(cleaned, cleaned)
