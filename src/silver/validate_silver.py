"""Silver-layer validation checks."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import col

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config import (
    BRONZE_SCHEMA,
    EXPECTED_MIN_FAILURE_ROWS,
    EXPECTED_ROW_COUNTS,
    SILVER_QUALITY_COLUMNS,
    SILVER_SCHEMA,
)
from silver.silver_utils import bronze_table_name, silver_table_name

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    name: str
    expected: str
    actual: str

    @property
    def passed(self) -> bool:
        return self.expected == self.actual


def _count_rows_with_code(df, code: str) -> int:
    return df.filter(col("quality_failure_reasons").contains(code)).count()


def validate_row_retention(spark: SparkSession, entity: str) -> ValidationResult:
    bronze_count = spark.table(bronze_table_name(entity)).count()
    silver_count = spark.table(silver_table_name(entity)).count()
    return ValidationResult(
        name=f"{entity}.row_retention",
        expected=str(bronze_count),
        actual=str(silver_count),
    )


def validate_quality_columns(spark: SparkSession, entity: str) -> ValidationResult:
    df = spark.table(silver_table_name(entity))
    missing = [column for column in SILVER_QUALITY_COLUMNS if column not in df.columns]
    if missing:
        return ValidationResult(
            name=f"{entity}.quality_columns",
            expected=f"columns present: {list(SILVER_QUALITY_COLUMNS)}",
            actual=f"missing: {missing}",
        )

    null_result = df.filter(col("quality_check_result").isNull()).count()
    null_processed = df.filter(col("_silver_processed_at").isNull()).count()
    if null_result > 0 or null_processed > 0:
        return ValidationResult(
            name=f"{entity}.quality_values",
            expected="quality columns populated",
            actual=(
                f"null quality_check_result={null_result}, "
                f"null _silver_processed_at={null_processed}"
            ),
        )

    return ValidationResult(
        name=f"{entity}.quality_columns",
        expected="quality columns present and populated",
        actual="quality columns present and populated",
    )


def validate_intentional_defects(spark: SparkSession) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    customers = spark.table(silver_table_name("customers"))
    orders = spark.table(silver_table_name("orders"))

    entity_frames = {
        "customers": customers,
        "orders": orders,
        "products": spark.table(silver_table_name("products")),
    }

    code_entity_map = {
        "COMPLETENESS_EMAIL": "customers",
        "COMPLETENESS_CUSTOMER_ID": "orders",
        "COMPLETENESS_PRODUCT_ID": "orders",
        "UNIQUENESS_CUSTOMER_ID": "customers",
        "UNIQUENESS_ORDER_ID": "orders",
        "UNIQUENESS_PRODUCT_ID": "products",
        "RI_CUSTOMER": "orders",
        "RI_PRODUCT": "orders",
    }

    for code, minimum in EXPECTED_MIN_FAILURE_ROWS.items():
        if minimum == 0:
            continue
        entity = code_entity_map[code]
        actual = _count_rows_with_code(entity_frames[entity], code)
        results.append(
            ValidationResult(
                name=f"defect.{code.lower()}",
                expected=f">= {minimum}",
                actual=str(actual),
            )
        )

    return results


def _parse_minimum(expected: str) -> int:
    return int(expected.replace(">=", "").strip())


def validate_quality_metrics(spark: SparkSession) -> list[ValidationResult]:
    table_name = f"{SILVER_SCHEMA}.quality_metrics"
    results: list[ValidationResult] = []

    if not spark.catalog.tableExists(table_name):
        results.append(
            ValidationResult(
                name="quality_metrics.exists",
                expected="table exists",
                actual="table missing",
            )
        )
        return results

    metrics_df = spark.table(table_name)
    row_count = metrics_df.count()
    results.append(
        ValidationResult(
            name="quality_metrics.row_count",
            expected="> 0",
            actual=str(row_count),
        )
    )

    required_entities = set(EXPECTED_ROW_COUNTS)
    present_entities = {
        row.entity for row in metrics_df.select("entity").distinct().collect()
    }
    for entity in required_entities:
        results.append(
            ValidationResult(
                name=f"quality_metrics.entity.{entity}",
                expected="present",
                actual="present" if entity in present_entities else "missing",
            )
        )

    return results


def validate_silver(spark: SparkSession) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    for entity in EXPECTED_ROW_COUNTS:
        results.append(validate_row_retention(spark, entity))
        results.append(validate_quality_columns(spark, entity))

    results.extend(validate_intentional_defects(spark))
    results.extend(validate_quality_metrics(spark))
    return results


def _result_passed(result: ValidationResult) -> bool:
    if result.name.startswith("defect."):
        return int(result.actual) >= _parse_minimum(result.expected)
    if result.name == "quality_metrics.row_count":
        return int(result.actual) > 0
    return result.passed


def print_validation_report(results: list[ValidationResult]) -> bool:
    print("\n=== Silver Validation ===")
    all_passed = True
    for result in results:
        passed = _result_passed(result)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {result.name}")
        if not passed:
            print(f"         expected: {result.expected}")
            print(f"         actual:   {result.actual}")
            all_passed = False

    print(f"\n  Overall: {'ALL CHECKS PASSED' if all_passed else 'VALIDATION FAILED'}")
    return all_passed


def main() -> int:
    from bronze.ingest_utils import get_spark

    spark = get_spark("silver-validate")
    results = validate_silver(spark)
    all_passed = print_validation_report(results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
