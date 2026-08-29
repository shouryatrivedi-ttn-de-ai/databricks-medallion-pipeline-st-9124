"""Gold-layer eligibility filters based on Silver quality_failure_reasons."""

from __future__ import annotations

from pyspark.sql import Column, DataFrame
from pyspark.sql.functions import col, lit

from config import GOLD_COMPLETED_ORDER_STATUS

ORDER_CRITICAL_FAILURES = (
    "COMPLETENESS_CUSTOMER_ID",
    "COMPLETENESS_PRODUCT_ID",
    "UNIQUENESS_ORDER_ID",
    "RI_CUSTOMER",
    "RI_PRODUCT",
    "TYPE_VALIDATION",
)

PRODUCT_CRITICAL_FAILURES = (
    "UNIQUENESS_PRODUCT_ID",
    "COMPLETENESS_PRODUCT_ID",
    "COMPLETENESS_PRODUCT_NAME",
    "TYPE_VALIDATION",
)

CUSTOMER_CRITICAL_FAILURES = ("UNIQUENESS_CUSTOMER_ID",)


def _has_critical_failure(codes: tuple[str, ...]) -> Column:
    """
    True when quality_failure_reasons is non-null and contains at least one code.
    NULL quality_failure_reasons is treated as eligible (no failure).
    """
    reasons = col("quality_failure_reasons")
    condition: Column | None = None
    for code in codes:
        match = reasons.isNotNull() & reasons.contains(code)
        condition = match if condition is None else (condition | match)
    if condition is None:
        return lit(False)
    return condition


def eligible_orders(orders_df: DataFrame) -> DataFrame:
    """Completed orders without critical order-level quality failures."""
    return orders_df.filter(
        (col("order_status") == GOLD_COMPLETED_ORDER_STATUS)
        & ~_has_critical_failure(ORDER_CRITICAL_FAILURES)
    )


def eligible_products(products_df: DataFrame) -> DataFrame:
    """Products without critical product-level quality failures."""
    return products_df.filter(~_has_critical_failure(PRODUCT_CRITICAL_FAILURES))


def eligible_customers(customers_df: DataFrame) -> DataFrame:
    """
    Customers eligible for segmentation and revenue aggregation.

    Only UNIQUENESS_CUSTOMER_ID excludes a customer. COMPLETENESS_EMAIL and other
    non-critical failures do not affect eligibility.
    """
    return customers_df.filter(~_has_critical_failure(CUSTOMER_CRITICAL_FAILURES))


def register_eligibility_views(
    orders_df: DataFrame,
    products_df: DataFrame,
    customers_df: DataFrame,
) -> None:
    """Register temp views used by Gold SQL aggregations."""
    eligible_orders(orders_df).createOrReplaceTempView("eligible_orders")
    eligible_products(products_df).createOrReplaceTempView("eligible_products")
    eligible_customers(customers_df).createOrReplaceTempView("eligible_customers")
