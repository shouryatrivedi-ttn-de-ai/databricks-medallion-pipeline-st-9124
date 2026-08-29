"""
Gold layer orchestrator.

Reads Silver tables, registers eligibility temp views, runs Gold SQL
aggregations, and validates outputs.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from bronze.ingest_utils import get_spark
from gold.eligibility import register_eligibility_views
from gold.gold_utils import (
    ensure_gold_schema,
    read_silver_table,
    run_gold_sql,
    verify_silver_tables,
)
from gold.validate_gold import print_validation_report, validate_gold

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GOLD_SQL_JOBS = (
    ("01_sales_by_product.sql", "sales_by_product"),
    ("02_revenue_by_customer.sql", "revenue_by_customer"),
    ("04_customer_segmentation.sql", "customer_segmentation"),
)


def main() -> int:
    spark = get_spark("gold-create-tables")
    ensure_gold_schema(spark)
    verify_silver_tables(spark)

    orders_df = read_silver_table(spark, "orders")
    products_df = read_silver_table(spark, "products")
    customers_df = read_silver_table(spark, "customers")

    register_eligibility_views(orders_df, products_df, customers_df)

    for sql_filename, table_name in GOLD_SQL_JOBS:
        logger.info("Running Gold aggregation: %s", table_name)
        run_gold_sql(spark, sql_filename, table_name)

    results = validate_gold(spark)
    all_passed = print_validation_report(results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
