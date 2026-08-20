"""Silver type and domain validation checks."""

from __future__ import annotations

from pyspark.sql import Column, DataFrame
from pyspark.sql.functions import col

from silver.quality_codes import (
    CUSTOMER_SEGMENTS,
    ORDER_STATUSES,
    TYPE_VALIDATION,
)
from silver.silver_utils import CheckMetric, build_check_metrics


def apply_type_validation_checks(entity: str, df: DataFrame) -> tuple[DataFrame, list[CheckMetric]]:
    total_rows = df.count()
    metrics: list[CheckMetric] = []
    conditions = _type_validation_conditions(entity)

    for check_name, condition in conditions:
        df, metric = build_check_metrics(
            entity,
            check_name,
            TYPE_VALIDATION,
            total_rows,
            df,
            condition,
        )
        metrics.append(metric)

    return df, metrics


def _type_validation_conditions(entity: str) -> list[tuple[str, Column]]:
    if entity == "customers":
        return [
            (
                "type_validation_segment",
                col("customer_segment").isNotNull()
                & ~col("customer_segment").isin(list(CUSTOMER_SEGMENTS)),
            ),
        ]

    if entity == "orders":
        return [
            (
                "type_validation_order_status",
                col("order_status").isNotNull()
                & ~col("order_status").isin(list(ORDER_STATUSES)),
            ),
            (
                "type_validation_quantity",
                col("quantity").isNotNull() & (col("quantity") <= 0),
            ),
        ]

    if entity == "products":
        return [
            (
                "type_validation_stock_quantity",
                col("stock_quantity").isNotNull() & (col("stock_quantity") < 0),
            ),
            (
                "type_validation_reorder_level",
                col("reorder_level").isNotNull() & (col("reorder_level") < 0),
            ),
        ]

    return []
