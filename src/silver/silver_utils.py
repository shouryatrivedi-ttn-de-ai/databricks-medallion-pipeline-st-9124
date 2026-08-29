"""Shared Silver layer utilities."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from pyspark.sql import Column, DataFrame, SparkSession
from pyspark.sql.functions import (
    col,
    concat,
    current_timestamp,
    lit,
    when,
)

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from bronze.ingest_utils import get_spark
from config import BRONZE_SCHEMA, SILVER_SCHEMA, SILVER_WRITE_MODE

logger = logging.getLogger(__name__)

PROCESS_ORDER = ("products", "customers", "orders")


@dataclass(frozen=True)
class CheckMetric:
    entity: str
    check_name: str
    total_rows: int
    failed_rows: int

    @property
    def passed_rows(self) -> int:
        return self.total_rows - self.failed_rows

    @property
    def pass_pct(self) -> float:
        if self.total_rows == 0:
            return 100.0
        return round((self.passed_rows / self.total_rows) * 100, 2)


def ensure_silver_schema(spark: SparkSession) -> None:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SILVER_SCHEMA}")


def bronze_table_name(entity: str) -> str:
    return f"{BRONZE_SCHEMA}.{entity}"


def silver_table_name(entity: str) -> str:
    return f"{SILVER_SCHEMA}.{entity}"


def read_bronze_table(spark: SparkSession, entity: str) -> DataFrame:
    table_name = bronze_table_name(entity)
    if not spark.catalog.tableExists(table_name):
        raise ValueError(f"Bronze table not found: {table_name}")
    return spark.table(table_name)


def init_quality_columns(df: DataFrame) -> DataFrame:
    return (
        df.withColumn("quality_check_result", lit("PASS"))
        .withColumn("quality_failure_reasons", lit(None).cast("string"))
    )


def append_failure_code(df: DataFrame, condition: Column, code: str) -> DataFrame:
    """Append a failure code and mark the row as FAIL when condition is true."""
    updated_reasons = when(
        condition,
        when(col("quality_failure_reasons").isNull(), lit(code)).otherwise(
            concat(col("quality_failure_reasons"), lit("|"), lit(code))
        ),
    ).otherwise(col("quality_failure_reasons"))

    return df.withColumn("quality_failure_reasons", updated_reasons).withColumn(
        "quality_check_result",
        when(condition, lit("FAIL")).otherwise(col("quality_check_result")),
    )


def count_failures(df: DataFrame, condition: Column) -> int:
    return df.filter(condition).count()


def metric_for_check(
    entity: str,
    check_name: str,
    total_rows: int,
    failed_rows: int,
) -> CheckMetric:
    return CheckMetric(
        entity=entity,
        check_name=check_name,
        total_rows=total_rows,
        failed_rows=failed_rows,
    )


def finalize_quality_columns(df: DataFrame) -> DataFrame:
    return df.withColumn("_silver_processed_at", current_timestamp())


def write_silver_table(df: DataFrame, entity: str) -> None:
    (
        df.write.format("delta")
        .mode(SILVER_WRITE_MODE)
        .option("overwriteSchema", "true")
        .saveAsTable(silver_table_name(entity))
    )


def write_quality_metrics(spark: SparkSession, metrics: list[CheckMetric]) -> None:
    if not metrics:
        return

    rows = [
        (
            metric.entity,
            metric.check_name,
            metric.total_rows,
            metric.passed_rows,
            metric.failed_rows,
            metric.pass_pct,
        )
        for metric in metrics
    ]

    metrics_df = spark.createDataFrame(
        rows,
        schema=(
            "entity string, check_name string, total_rows long, "
            "passed_rows long, failed_rows long, pass_pct double"
        ),
    ).withColumn("run_timestamp", current_timestamp())

    (
        metrics_df.write.format("delta")
        .mode(SILVER_WRITE_MODE)
        .option("overwriteSchema", "true")
        .saveAsTable(f"{SILVER_SCHEMA}.quality_metrics")
    )


def build_check_metrics(
    entity: str,
    check_name: str,
    failure_code: str,
    total_rows: int,
    df: DataFrame,
    condition: Column,
) -> tuple[DataFrame, CheckMetric]:
    updated_df = append_failure_code(df, condition, failure_code)
    failed_rows = count_failures(updated_df, condition)
    return updated_df, metric_for_check(entity, check_name, total_rows, failed_rows)
