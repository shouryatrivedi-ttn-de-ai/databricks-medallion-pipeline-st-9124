"""Gold-layer validation checks."""

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
    EXPECTED_GOLD_TABLES,
    SEGMENT_TYPES,
)
from gold.eligibility import eligible_customers, eligible_orders
from gold.gold_utils import gold_table_name, read_silver_table, silver_table_name

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    name: str
    expected: str
    actual: str

    @property
    def passed(self) -> bool:
        return self.expected == self.actual


def _gte_result(name: str, minimum: int, actual: int) -> ValidationResult:
    return ValidationResult(name=name, expected=f">= {minimum}", actual=str(actual))


def validate_tables_exist(spark: SparkSession) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    for table in EXPECTED_GOLD_TABLES:
        full_name = gold_table_name(table)
        exists = spark.catalog.tableExists(full_name)
        results.append(
            ValidationResult(
                name=f"gold_table.exists.{table}",
                expected="exists",
                actual="exists" if exists else "missing",
            )
        )
    return results


def validate_row_counts(spark: SparkSession) -> list[ValidationResult]:
    sales_count = spark.table(gold_table_name("sales_by_product")).count()
    revenue_count = spark.table(gold_table_name("revenue_by_customer")).count()
    return [
        _gte_result("sales_by_product.row_count", 1, sales_count),
        _gte_result("revenue_by_customer.row_count", 1, revenue_count),
    ]


def validate_segmentation(spark: SparkSession) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    segmentation_df = spark.table(gold_table_name("customer_segmentation"))

    segment_labels = {
        row.segment_type for row in segmentation_df.select("segment_type").distinct().collect()
    }
    invalid_labels = segment_labels - set(SEGMENT_TYPES)
    results.append(
        ValidationResult(
            name="customer_segmentation.valid_labels",
            expected=f"subset of {list(SEGMENT_TYPES)}",
            actual="valid" if not invalid_labels else f"invalid: {sorted(invalid_labels)}",
        )
    )

    eligible_customer_count = eligible_customers(
        read_silver_table(spark, "customers")
    ).count()
    segmented_customer_count = segmentation_df.agg({"customer_count": "sum"}).collect()[0][0]
    results.append(
        ValidationResult(
            name="customer_segmentation.customer_count_total",
            expected=str(eligible_customer_count),
            actual=str(segmented_customer_count),
        )
    )

    inactive_count = (
        segmentation_df.filter(col("segment_type") == "Inactive")
        .select("customer_count")
        .collect()
    )
    inactive_value = inactive_count[0][0] if inactive_count else 0
    results.append(_gte_result("customer_segmentation.inactive_count", 1, inactive_value))

    return results


def validate_non_negative_metrics(spark: SparkSession) -> list[ValidationResult]:
    results: list[ValidationResult] = []

    sales_bad = spark.table(gold_table_name("sales_by_product")).filter(
        (col("total_orders") < 0)
        | (col("total_revenue") < 0)
        | (
            (col("total_orders") > 0)
            & (
                col("avg_order_value").isNull()
                | (col("avg_order_value") < 0)
            )
        )
    ).count()

    revenue_bad = spark.table(gold_table_name("revenue_by_customer")).filter(
        (col("total_orders") < 0)
        | (col("total_revenue") < 0)
        | (col("lifetime_value_actual") < 0)
        | (
            (col("total_orders") > 0)
            & (
                col("avg_order_value").isNull()
                | (col("avg_order_value") < 0)
            )
        )
    ).count()

    segmentation_bad = spark.table(gold_table_name("customer_segmentation")).filter(
        (col("customer_count") < 0)
        | (col("avg_revenue") < 0)
        | (col("total_revenue") < 0)
    ).count()

    results.append(
        ValidationResult(
            name="sales_by_product.non_negative_metrics",
            expected="0 invalid rows",
            actual=f"{sales_bad} invalid rows",
        )
    )
    results.append(
        ValidationResult(
            name="revenue_by_customer.non_negative_metrics",
            expected="0 invalid rows",
            actual=f"{revenue_bad} invalid rows",
        )
    )
    results.append(
        ValidationResult(
            name="customer_segmentation.non_negative_metrics",
            expected="0 invalid rows",
            actual=f"{segmentation_bad} invalid rows",
        )
    )
    return results


def validate_eligible_source_usage(spark: SparkSession) -> list[ValidationResult]:
    """Confirm Gold revenue totals match eligible PASS + Completed Silver orders."""
    results: list[ValidationResult] = []

    eligible_orders_df = eligible_orders(read_silver_table(spark, "orders"))
    expected_revenue = float(
        eligible_orders_df.agg({"total_amount": "sum"}).collect()[0][0] or 0
    )
    expected_order_count = eligible_orders_df.select("order_id").distinct().count()

    sales_df = spark.table(gold_table_name("sales_by_product"))
    revenue_df = spark.table(gold_table_name("revenue_by_customer"))
    segmentation_df = spark.table(gold_table_name("customer_segmentation"))

    sales_revenue = float(sales_df.agg({"total_revenue": "sum"}).collect()[0][0] or 0)
    customer_revenue = float(revenue_df.agg({"total_revenue": "sum"}).collect()[0][0] or 0)
    segmentation_revenue = float(
        segmentation_df.agg({"total_revenue": "sum"}).collect()[0][0] or 0
    )

    sales_order_count = int(sales_df.agg({"total_orders": "sum"}).collect()[0][0] or 0)
    customer_order_count = int(revenue_df.agg({"total_orders": "sum"}).collect()[0][0] or 0)

    results.append(
        ValidationResult(
            name="sales_by_product.eligible_revenue_total",
            expected=f"{expected_revenue:.2f}",
            actual=f"{sales_revenue:.2f}",
        )
    )
    results.append(
        ValidationResult(
            name="revenue_by_customer.eligible_revenue_total",
            expected=f"{expected_revenue:.2f}",
            actual=f"{customer_revenue:.2f}",
        )
    )
    results.append(
        ValidationResult(
            name="customer_segmentation.eligible_revenue_total",
            expected=f"{expected_revenue:.2f}",
            actual=f"{segmentation_revenue:.2f}",
        )
    )
    results.append(
        ValidationResult(
            name="revenue_by_customer.eligible_order_count",
            expected=str(expected_order_count),
            actual=str(customer_order_count),
        )
    )
    results.append(
        ValidationResult(
            name="sales_by_product.eligible_order_count",
            expected=str(expected_order_count),
            actual=str(sales_order_count),
        )
    )

    return results


def validate_gold(spark: SparkSession) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    results.extend(validate_tables_exist(spark))
    results.extend(validate_row_counts(spark))
    results.extend(validate_segmentation(spark))
    results.extend(validate_non_negative_metrics(spark))
    results.extend(validate_eligible_source_usage(spark))
    return results


def _result_passed(result: ValidationResult) -> bool:
    if result.name.endswith(".row_count") or result.name.endswith(".inactive_count"):
        return int(result.actual) >= int(result.expected.replace(">= ", ""))
    if result.name.endswith(".non_negative_metrics"):
        return result.actual == "0 invalid rows"
    if result.name.endswith(".eligible_revenue_total"):
        return float(result.actual) == float(result.expected)
    return result.passed


def print_validation_report(results: list[ValidationResult]) -> bool:
    print("\n=== Gold Validation ===")
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

    spark = get_spark("gold-validate")
    results = validate_gold(spark)
    all_passed = print_validation_report(results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
