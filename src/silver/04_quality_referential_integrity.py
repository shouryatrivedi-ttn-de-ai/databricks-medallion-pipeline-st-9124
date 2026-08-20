"""Silver referential integrity checks for orders."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql.functions import col

from silver.quality_codes import RI_CUSTOMER, RI_PRODUCT
from silver.silver_utils import CheckMetric, build_check_metrics


def _distinct_non_null_ids(df: DataFrame, column: str) -> list:
    rows = df.select(column).distinct().filter(col(column).isNotNull()).collect()
    return [row[column] for row in rows]


def apply_referential_integrity_checks(
    entity: str,
    df: DataFrame,
    silver_customers: DataFrame,
    silver_products: DataFrame,
) -> tuple[DataFrame, list[CheckMetric]]:
    if entity != "orders":
        return df, []

    total_rows = df.count()
    metrics: list[CheckMetric] = []

    valid_customer_ids = _distinct_non_null_ids(silver_customers, "customer_id")
    valid_product_ids = _distinct_non_null_ids(silver_products, "product_id")

    orphan_customer_condition = col("customer_id").isNotNull() & ~col("customer_id").isin(
        valid_customer_ids
    )
    df, metric = build_check_metrics(
        entity,
        "ri_customer",
        RI_CUSTOMER,
        total_rows,
        df,
        orphan_customer_condition,
    )
    metrics.append(metric)

    orphan_product_condition = col("product_id").isNotNull() & ~col("product_id").isin(
        valid_product_ids
    )
    df, metric = build_check_metrics(
        entity,
        "ri_product",
        RI_PRODUCT,
        total_rows,
        df,
        orphan_product_condition,
    )
    metrics.append(metric)

    return df, metrics
