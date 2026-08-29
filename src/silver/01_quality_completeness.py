"""Silver completeness quality checks."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql.functions import col

from silver.quality_codes import (
    COMPLETENESS_CUSTOMER_ID,
    COMPLETENESS_EMAIL,
    COMPLETENESS_PRODUCT_ID,
    COMPLETENESS_PRODUCT_NAME,
)
from silver.silver_utils import CheckMetric, build_check_metrics


def apply_completeness_checks(entity: str, df: DataFrame) -> tuple[DataFrame, list[CheckMetric]]:
    total_rows = df.count()
    metrics: list[CheckMetric] = []

    if entity == "customers":
        df, metric = build_check_metrics(
            entity,
            "completeness_email",
            COMPLETENESS_EMAIL,
            total_rows,
            df,
            col("email").isNull(),
        )
        metrics.append(metric)

    elif entity == "orders":
        df, metric = build_check_metrics(
            entity,
            "completeness_customer_id",
            COMPLETENESS_CUSTOMER_ID,
            total_rows,
            df,
            col("customer_id").isNull(),
        )
        metrics.append(metric)

        df, metric = build_check_metrics(
            entity,
            "completeness_product_id",
            COMPLETENESS_PRODUCT_ID,
            total_rows,
            df,
            col("product_id").isNull(),
        )
        metrics.append(metric)

    elif entity == "products":
        df, metric = build_check_metrics(
            entity,
            "completeness_product_id",
            COMPLETENESS_PRODUCT_ID,
            total_rows,
            df,
            col("product_id").isNull(),
        )
        metrics.append(metric)

        df, metric = build_check_metrics(
            entity,
            "completeness_product_name",
            COMPLETENESS_PRODUCT_NAME,
            total_rows,
            df,
            col("product_name").isNull(),
        )
        metrics.append(metric)

    return df, metrics
