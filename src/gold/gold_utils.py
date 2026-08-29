"""Shared Gold layer utilities."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config import GOLD_SCHEMA, GOLD_WRITE_MODE, SEGMENTATION_HIGH_VALUE_THRESHOLD, SILVER_SCHEMA

logger = logging.getLogger(__name__)

GOLD_SQL_DIR = Path(__file__).resolve().parent


def ensure_gold_schema(spark: SparkSession) -> None:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {GOLD_SCHEMA}")


def silver_table_name(entity: str) -> str:
    return f"{SILVER_SCHEMA}.{entity}"


def gold_table_name(table: str) -> str:
    return f"{GOLD_SCHEMA}.{table}"


def read_silver_table(spark: SparkSession, entity: str) -> DataFrame:
    table_name = silver_table_name(entity)
    if not spark.catalog.tableExists(table_name):
        raise ValueError(f"Silver table not found: {table_name}")
    return spark.table(table_name)


def render_sql(sql_filename: str) -> str:
    sql_path = GOLD_SQL_DIR / sql_filename
    template = sql_path.read_text(encoding="utf-8")
    return template.replace(
        "{{SEGMENTATION_HIGH_VALUE_THRESHOLD}}",
        str(SEGMENTATION_HIGH_VALUE_THRESHOLD),
    )


def run_gold_sql(spark: SparkSession, sql_filename: str, table_name: str) -> int:
    query = render_sql(sql_filename)
    result_df = spark.sql(query)
    row_count = result_df.count()
    (
        result_df.write.format("delta")
        .mode(GOLD_WRITE_MODE)
        .option("overwriteSchema", "true")
        .saveAsTable(gold_table_name(table_name))
    )
    logger.info("Wrote %s rows to %s", row_count, gold_table_name(table_name))
    return row_count


def verify_silver_tables(spark: SparkSession) -> None:
    for entity in ("products", "customers", "orders"):
        table_name = silver_table_name(entity)
        if not spark.catalog.tableExists(table_name):
            raise ValueError(f"Required Silver table not found: {table_name}")
