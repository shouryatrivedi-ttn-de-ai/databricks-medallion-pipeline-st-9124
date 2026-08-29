"""
Shared pipeline configuration.

Values can be overridden with environment variables for Databricks runs.
No secrets or credentials belong in this module.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Local default: repo / data / ; override on Databricks via DATA_PATH env var
DEFAULT_DATA_PATH = str(REPO_ROOT / "data")

DATA_PATH = os.getenv("DATA_PATH", DEFAULT_DATA_PATH)
BRONZE_SCHEMA = os.getenv("BRONZE_SCHEMA", "workspace.bronze")
BRONZE_WRITE_MODE = os.getenv("BRONZE_WRITE_MODE", "overwrite")

SILVER_SCHEMA = os.getenv("SILVER_SCHEMA", "workspace.silver")
SILVER_WRITE_MODE = os.getenv("SILVER_WRITE_MODE", "overwrite")

# Expected row counts from sample data generator (assignment targets)
EXPECTED_ROW_COUNTS: dict[str, int] = {
    "customers": 10_000,
    "orders": 100_000,
    "products": 500,
}

# Minimum failed-row counts for intentional defects (Silver validation)
EXPECTED_MIN_FAILURE_ROWS: dict[str, int] = {
    "COMPLETENESS_EMAIL": 50,
    "COMPLETENESS_CUSTOMER_ID": 100,
    "COMPLETENESS_PRODUCT_ID": 200,
    "UNIQUENESS_CUSTOMER_ID": 20,
    "UNIQUENESS_ORDER_ID": 40,
    "UNIQUENESS_PRODUCT_ID": 0,
    "RI_CUSTOMER": 50,
    "RI_PRODUCT": 30,
}

SILVER_QUALITY_COLUMNS = (
    "quality_check_result",
    "quality_failure_reasons",
    "_silver_processed_at",
)

GOLD_SCHEMA = os.getenv("GOLD_SCHEMA", "workspace.gold")
GOLD_WRITE_MODE = os.getenv("GOLD_WRITE_MODE", "overwrite")
GOLD_COMPLETED_ORDER_STATUS = os.getenv("GOLD_COMPLETED_ORDER_STATUS", "Completed")
SEGMENTATION_HIGH_VALUE_THRESHOLD = float(
    os.getenv("SEGMENTATION_HIGH_VALUE_THRESHOLD", "1000")
)

SEGMENT_TYPES = ("High-Value", "Repeat", "One-Time", "Inactive")

EXPECTED_GOLD_TABLES = (
    "sales_by_product",
    "revenue_by_customer",
    "customer_segmentation",
)

CSV_FILES: dict[str, str] = {
    "customers": "customers.csv",
    "orders": "orders.csv",
    "products": "products.csv",
}

INGEST_METADATA_COLUMNS = ("_ingest_timestamp", "_source_file")
