"""
Shared pipeline configuration.

Values can be overridden with environment variables for Databricks runs.
No secrets or credentials belong in this module.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Local default: repo / data / ; override on Databricks (e.g. /dbfs/FileStore/medallion/data/)
DEFAULT_DATA_PATH = str(REPO_ROOT / "data")

DATA_PATH = os.getenv("DATA_PATH", DEFAULT_DATA_PATH)
BRONZE_SCHEMA = os.getenv("BRONZE_SCHEMA", "bronze")
BRONZE_WRITE_MODE = os.getenv("BRONZE_WRITE_MODE", "overwrite")

# Expected row counts from sample data generator (assignment targets)
EXPECTED_ROW_COUNTS: dict[str, int] = {
    "customers": 10_000,
    "orders": 100_000,
    "products": 500,
}

CSV_FILES: dict[str, str] = {
    "customers": "customers.csv",
    "orders": "orders.csv",
    "products": "products.csv",
}

INGEST_METADATA_COLUMNS = ("_ingest_timestamp", "_source_file")
