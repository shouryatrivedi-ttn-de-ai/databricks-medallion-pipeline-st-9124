"""
Bronze ingestion orchestrator.

Ingest order: products -> customers -> orders (parents before child for traceability).
Aborts if a source CSV is missing or empty. Runs Bronze validation at the end.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from bronze.ingest_utils import ensure_bronze_schema, get_spark, ingest_entity
from bronze.validate_bronze import print_validation_report, validate_bronze

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

INGEST_ORDER = ("products", "customers", "orders")


def main() -> int:
    spark = get_spark("bronze-ingest-all")
    ensure_bronze_schema(spark)

    for entity in INGEST_ORDER:
        ingest_entity(spark, entity)

    results = validate_bronze(spark)
    all_passed = print_validation_report(results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
