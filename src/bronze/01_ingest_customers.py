"""Bronze ingest: customers.csv -> bronze.customers"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from bronze.ingest_utils import ensure_bronze_schema, get_spark, ingest_entity

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main() -> int:
    spark = get_spark("bronze-ingest-customers")
    ensure_bronze_schema(spark)
    ingest_entity(spark, "customers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
