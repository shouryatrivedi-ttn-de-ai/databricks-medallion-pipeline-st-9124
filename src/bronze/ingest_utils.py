"""Shared Bronze ingestion helpers."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import current_timestamp, lit
from pyspark.sql.types import StructType

# Allow imports from src/ when run as a script on Databricks or locally
SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config import BRONZE_SCHEMA, BRONZE_WRITE_MODE, CSV_FILES, DATA_PATH
from bronze.schemas import ENTITY_SCHEMAS

logger = logging.getLogger(__name__)


def get_spark(app_name: str) -> SparkSession:
    """Create or reuse a SparkSession with Delta Lake support where available."""
    builder = SparkSession.builder.appName(app_name)

    try:
        from delta import configure_spark_with_delta_pip

        builder = configure_spark_with_delta_pip(builder)
    except ImportError:
        # Databricks runtimes include Delta Lake by default.
        builder = builder.config(
            "spark.sql.extensions",
            "io.delta.sql.DeltaSparkSessionExtension",
        ).config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )

    return builder.getOrCreate()


def ensure_bronze_schema(spark: SparkSession) -> None:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {BRONZE_SCHEMA}")


def resolve_csv_path(entity: str) -> str:
    filename = CSV_FILES[entity]

    if DATA_PATH.startswith("/Volumes/"):
        return f"{DATA_PATH.rstrip('/')}/{filename}"

    path = Path(DATA_PATH) / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Missing source CSV for '{entity}': {path}. "
            f"Set DATA_PATH or generate sample data first."
        )
    if path.stat().st_size == 0:
        raise ValueError(f"Source CSV is empty for '{entity}': {path}")
    return str(path.resolve())


def read_csv_with_schema(
    spark: SparkSession,
    source_path: str,
    schema: StructType,
) -> DataFrame:
    """
    Read CSV with the entity's explicit Spark schema.

    Empty fields are treated as NULL (intentional completeness defects).
    FAILFAST mode ensures malformed values raise an error instead of
    being silently converted to NULL during ingest.
    """
    return (
        spark.read.schema(schema)
        .option("header", True)
        .option("nullValue", "")
        .option("dateFormat", "yyyy-MM-dd")
        .option("mode", "FAILFAST")
        .csv(source_path)
    )


def add_ingest_metadata(df: DataFrame, source_path: str) -> DataFrame:
    source_name = Path(source_path).name
    return df.withColumn("_ingest_timestamp", current_timestamp()).withColumn(
        "_source_file", lit(source_name)
    )


def write_delta_table(df: DataFrame, table_name: str) -> None:
    (
        df.write.format("delta")
        .mode(BRONZE_WRITE_MODE)
        .option("overwriteSchema", "true")
        .saveAsTable(table_name)
    )


def append_ingestion_log(
    spark: SparkSession,
    entity: str,
    row_count: int,
    source_path: str,
) -> None:
    log_df = spark.createDataFrame(
        [(entity, row_count, source_path)],
        schema="entity string, row_count int, source_path string",
    ).withColumn("ingest_timestamp", current_timestamp())

    table_name = f"{BRONZE_SCHEMA}.ingestion_log"
    write_mode = "overwrite" if not spark.catalog.tableExists(table_name) else "append"
    log_df.write.format("delta").mode(write_mode).saveAsTable(table_name)


def ingest_entity(spark: SparkSession, entity: str) -> int:
    """
    Ingest one CSV entity into Bronze Delta.

    Returns the number of rows written.
    """
    schema = ENTITY_SCHEMAS[entity]
    source_path = resolve_csv_path(entity)
    table_name = f"{BRONZE_SCHEMA}.{entity}"

    logger.info("Ingesting %s from %s -> %s", entity, source_path, table_name)

    source_df = read_csv_with_schema(spark, source_path, schema)
    bronze_df = add_ingest_metadata(source_df, source_path)

    write_delta_table(bronze_df, table_name)
    row_count = bronze_df.count()

    append_ingestion_log(spark, entity, row_count, source_path)
    logger.info("Ingested %s rows into %s", row_count, table_name)
    return row_count
