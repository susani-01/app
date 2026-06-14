"""Load JSONL source files into PostgreSQL."""

from __future__ import annotations

import os
from pathlib import Path

from src.db.session import SessionLocal
from src.etl.loader import run_etl


def main() -> None:
    classification_file = Path(
        os.getenv("CLASSIFICATION_FILE", "data/construction_classification.jsonl"),
    )
    price_file = Path(os.getenv("PRICE_FILE", "data/std_market_price.jsonl"))

    if not classification_file.exists():
        raise FileNotFoundError(f"Missing classification file: {classification_file}")
    if not price_file.exists():
        raise FileNotFoundError(f"Missing price file: {price_file}")

    with SessionLocal() as session:
        stats = run_etl(session, classification_file, price_file)

    print("\n=== ETL Complete ===")
    print(f"Work divisions:       {stats.work_divisions:,}")
    print(f"Units:                  {stats.units:,}")
    print(f"Classification nodes:   {stats.classification_nodes:,}")
    print(f"Quantity items:         {stats.quantity_items:,}")
    print(f"Market prices:          {stats.market_prices:,}")
    print(f"Skipped price rows:     {stats.skipped_price_rows:,}")
    print(f"Unmapped unit strings:  {len(stats.unmapped_units):,}")


if __name__ == "__main__":
    main()
