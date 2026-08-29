"""Silver uniqueness quality checks."""

from __future__ import annotations

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, count
from pyspark.sql.window import Window

from silver.quality_codes import (
    UNIQUENESS_CUSTOMER_ID,
    UNIQUENESS_ORDER_ID,
    UNIQUENESS_PRODUCT_ID,
)
from silver.silver_utils import (
    CheckMetric,
    append_failure_code,
    count_failures,
    metric_for_check,
)


def apply_uniqueness_checks(entity: str, df: DataFrame) -> tuple[DataFrame, list[CheckMetric]]:
    total_rows = df.count()
    metrics: list[CheckMetric] = []

    if entity == "customers":
        key_col = "customer_id"
        failure_code = UNIQUENESS_CUSTOMER_ID
        check_name = "uniqueness_customer_id"
    elif entity == "orders":
        key_col = "order_id"
        failure_code = UNIQUENESS_ORDER_ID
        check_name = "uniqueness_order_id"
    elif entity == "products":
        key_col = "product_id"
        failure_code = UNIQUENESS_PRODUCT_ID
        check_name = "uniqueness_product_id"
    else:
        return df, metrics

    window_spec = Window.partitionBy(key_col)
    df = df.withColumn("_duplicate_count", count(col(key_col)).over(window_spec))
    duplicate_condition = col("_duplicate_count") > 1

    df = append_failure_code(df, duplicate_condition, failure_code)
    failed_rows = count_failures(df, duplicate_condition)
    metrics.append(metric_for_check(entity, check_name, total_rows, failed_rows))

    return df.drop("_duplicate_count"), metrics
