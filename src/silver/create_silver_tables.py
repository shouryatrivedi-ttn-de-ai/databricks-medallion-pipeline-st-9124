"""
Silver layer orchestrator.

Processing order: products -> customers -> orders.
Reads Bronze Delta tables, applies quality checks, writes Silver Delta tables
and quality_metrics, then runs validation.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from bronze.ingest_utils import get_spark
from config import SILVER_SCHEMA
from silver.silver_utils import (
    CheckMetric,
    PROCESS_ORDER,
    ensure_silver_schema,
    finalize_quality_columns,
    init_quality_columns,
    read_bronze_table,
    silver_table_name,
    write_quality_metrics,
    write_silver_table,
)
from silver.validate_silver import print_validation_report, validate_silver

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _load_check_modules() -> dict:
    base = Path(__file__).resolve().parent
    mapping = {
        "completeness": "01_quality_completeness.py",
        "uniqueness": "02_quality_uniqueness.py",
        "type_validation": "03_quality_type_validation.py",
        "referential_integrity": "04_quality_referential_integrity.py",
    }
    modules = {}
    for name, filename in mapping.items():
        spec = importlib.util.spec_from_file_location(f"silver_{name}", base / filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules[name] = module
    return modules


def process_entity(
    spark: SparkSession,
    entity: str,
    check_modules: dict,
    silver_customers: DataFrame | None = None,
    silver_products: DataFrame | None = None,
) -> tuple[DataFrame, list[CheckMetric]]:
    logger.info("Processing Silver entity: %s", entity)
    bronze_df = read_bronze_table(spark, entity)
    bronze_count = bronze_df.count()
    logger.info("  Bronze rows: %s", bronze_count)

    df = init_quality_columns(bronze_df)
    metrics: list[CheckMetric] = []

    df, completeness_metrics = check_modules["completeness"].apply_completeness_checks(
        entity, df
    )
    metrics.extend(completeness_metrics)

    df, uniqueness_metrics = check_modules["uniqueness"].apply_uniqueness_checks(entity, df)
    metrics.extend(uniqueness_metrics)

    df, type_metrics = check_modules["type_validation"].apply_type_validation_checks(
        entity, df
    )
    metrics.extend(type_metrics)

    if entity == "orders":
        if silver_customers is None or silver_products is None:
            raise ValueError("Silver parent tables required before processing orders")
        df, ri_metrics = check_modules[
            "referential_integrity"
        ].apply_referential_integrity_checks(
            entity, df, silver_customers, silver_products
        )
        metrics.extend(ri_metrics)

    df = finalize_quality_columns(df)
    silver_count = df.count()
    if silver_count != bronze_count:
        raise ValueError(
            f"Row retention violated for {entity}: bronze={bronze_count}, silver={silver_count}"
        )

    write_silver_table(df, entity)
    logger.info("  Wrote %s rows to %s", silver_count, silver_table_name(entity))
    return df, metrics


def main() -> int:
    spark = get_spark("silver-create-tables")
    ensure_silver_schema(spark)
    check_modules = _load_check_modules()

    all_metrics: list[CheckMetric] = []
    silver_customers = None
    silver_products = None

    for entity in PROCESS_ORDER:
        df, metrics = process_entity(
            spark,
            entity,
            check_modules,
            silver_customers=silver_customers,
            silver_products=silver_products,
        )
        all_metrics.extend(metrics)
        if entity == "products":
            silver_products = df
        elif entity == "customers":
            silver_customers = df

    write_quality_metrics(spark, all_metrics)
    logger.info("Wrote quality metrics to %s.quality_metrics", SILVER_SCHEMA)

    results = validate_silver(spark)
    all_passed = print_validation_report(results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
