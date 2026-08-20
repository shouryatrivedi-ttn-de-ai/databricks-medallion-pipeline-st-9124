"""Explicit Spark schemas for Bronze CSV sources."""

from pyspark.sql.types import (
    DateType,
    DecimalType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

CUSTOMERS_SCHEMA = StructType(
    [
        StructField("customer_id", IntegerType(), nullable=True),
        StructField("customer_name", StringType(), nullable=True),
        StructField("email", StringType(), nullable=True),
        StructField("country", StringType(), nullable=True),
        StructField("signup_date", DateType(), nullable=True),
        StructField("customer_segment", StringType(), nullable=True),
        StructField("lifetime_value", DecimalType(18, 2), nullable=True),
    ]
)

ORDERS_SCHEMA = StructType(
    [
        StructField("order_id", IntegerType(), nullable=True),
        StructField("customer_id", IntegerType(), nullable=True),
        StructField("order_date", DateType(), nullable=True),
        StructField("product_id", IntegerType(), nullable=True),
        StructField("quantity", IntegerType(), nullable=True),
        StructField("unit_price", DecimalType(18, 2), nullable=True),
        StructField("total_amount", DecimalType(18, 2), nullable=True),
        StructField("order_status", StringType(), nullable=True),
        StructField("payment_date", DateType(), nullable=True),
    ]
)

PRODUCTS_SCHEMA = StructType(
    [
        StructField("product_id", IntegerType(), nullable=True),
        StructField("product_name", StringType(), nullable=True),
        StructField("category", StringType(), nullable=True),
        StructField("price", DecimalType(18, 2), nullable=True),
        StructField("cost", DecimalType(18, 2), nullable=True),
        StructField("stock_quantity", IntegerType(), nullable=True),
        StructField("reorder_level", IntegerType(), nullable=True),
    ]
)

INGESTION_LOG_SCHEMA = StructType(
    [
        StructField("entity", StringType(), nullable=False),
        StructField("row_count", IntegerType(), nullable=False),
        StructField("ingest_timestamp", TimestampType(), nullable=False),
        StructField("source_path", StringType(), nullable=False),
    ]
)

ENTITY_SCHEMAS: dict[str, StructType] = {
    "customers": CUSTOMERS_SCHEMA,
    "orders": ORDERS_SCHEMA,
    "products": PRODUCTS_SCHEMA,
}
