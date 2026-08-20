"""Bronze-layer validation checks."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from pyspark.sql import SparkSession

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config import BRONZE_SCHEMA, EXPECTED_ROW_COUNTS, INGEST_METADATA_COLUMNS

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    name: str
    expected: str
    actual: str

    @property
    def passed(self) -> bool:
        return self.expected == self.actual


def validate_row_count(spark: SparkSession, entity: str) -> ValidationResult:
    table_name = f"{BRONZE_SCHEMA}.{entity}"
    expected = EXPECTED_ROW_COUNTS[entity]
    actual = spark.table(table_name).count()
    return ValidationResult(
        name=f"{entity}.row_count",
        expected=str(expected),
        actual=str(actual),
    )


def validate_ingest_metadata(spark: SparkSession, entity: str) -> ValidationResult:
    table_name = f"{BRONZE_SCHEMA}.{entity}"
    df = spark.table(table_name)
    columns = df.columns

    missing = [col_name for col_name in INGEST_METADATA_COLUMNS if col_name not in columns]
    if missing:
        return ValidationResult(
            name=f"{entity}.metadata_columns",
            expected=f"columns present: {list(INGEST_METADATA_COLUMNS)}",
            actual=f"missing: {missing}",
        )

    null_timestamp = df.filter("_ingest_timestamp IS NULL").count()
    null_source = df.filter("_source_file IS NULL").count()
    if null_timestamp > 0 or null_source > 0:
        return ValidationResult(
            name=f"{entity}.metadata_values",
            expected="all metadata populated",
            actual=(
                f"null _ingest_timestamp={null_timestamp}, "
                f"null _source_file={null_source}"
            ),
        )

    return ValidationResult(
        name=f"{entity}.metadata",
        expected="metadata present and populated",
        actual="metadata present and populated",
    )


def validate_ingestion_log(spark: SparkSession) -> list[ValidationResult]:
    table_name = f"{BRONZE_SCHEMA}.ingestion_log"
    results: list[ValidationResult] = []

    if not spark.catalog.tableExists(table_name):
        results.append(
            ValidationResult(
                name="ingestion_log.exists",
                expected="table exists",
                actual="table missing",
            )
        )
        return results

    log_df = spark.table(table_name)
    entities = {row.entity for row in log_df.select("entity").distinct().collect()}

    for entity in EXPECTED_ROW_COUNTS:
        results.append(
            ValidationResult(
                name=f"ingestion_log.entity.{entity}",
                expected="logged",
                actual="logged" if entity in entities else "missing",
            )
        )

    return results


def validate_bronze(spark: SparkSession) -> list[ValidationResult]:
    """Run all Bronze validation checks."""
    results: list[ValidationResult] = []
    for entity in EXPECTED_ROW_COUNTS:
        results.append(validate_row_count(spark, entity))
        results.append(validate_ingest_metadata(spark, entity))
    results.extend(validate_ingestion_log(spark))
    return results


def print_validation_report(results: list[ValidationResult]) -> bool:
    print("\n=== Bronze Validation ===")
    all_passed = True
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"  [{status}] {result.name}")
        if not result.passed:
            print(f"         expected: {result.expected}")
            print(f"         actual:   {result.actual}")
            all_passed = False

    print(f"\n  Overall: {'ALL CHECKS PASSED' if all_passed else 'VALIDATION FAILED'}")
    return all_passed


def main() -> int:
    from bronze.ingest_utils import get_spark

    spark = get_spark("bronze-validate")
    results = validate_bronze(spark)
    all_passed = print_validation_report(results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
