-- Bronze schema setup for the medallion pipeline.
-- Delta tables are created on first ingest via saveAsTable; this script ensures the schema exists.

CREATE SCHEMA IF NOT EXISTS bronze;

-- Entity tables (created automatically on ingest):
--   bronze.customers
--   bronze.orders
--   bronze.products
--   bronze.ingestion_log
--
-- Entity tables mirror CSV columns plus:
--   _ingest_timestamp  TIMESTAMP
--   _source_file       STRING
--
-- ingestion_log columns:
--   entity             STRING
--   row_count          BIGINT
--   ingest_timestamp   TIMESTAMP
--   source_path        STRING

-- Silver schema setup for the medallion pipeline.
-- Delta tables are created on first Silver run via saveAsTable.

CREATE SCHEMA IF NOT EXISTS workspace.silver;

-- Entity tables (created automatically on Silver processing):
--   workspace.silver.customers
--   workspace.silver.orders
--   workspace.silver.products
--   workspace.silver.quality_metrics
--
-- Silver entity tables include all Bronze columns plus:
--   quality_check_result     STRING
--   quality_failure_reasons  STRING
--   _silver_processed_at     TIMESTAMP
--
-- quality_metrics columns:
--   entity         STRING
--   check_name     STRING
--   total_rows     BIGINT
--   passed_rows    BIGINT
--   failed_rows    BIGINT
--   pass_pct       DOUBLE
--   run_timestamp  TIMESTAMP

-- Gold schema setup for the medallion pipeline.
-- Delta tables are created on first Gold run via saveAsTable.

CREATE SCHEMA IF NOT EXISTS workspace.gold;

-- Aggregation tables (created automatically on Gold processing):
--   workspace.gold.sales_by_product
--   workspace.gold.revenue_by_customer
--   workspace.gold.customer_segmentation
--
-- sales_by_product columns:
--   product_id, product_name, category,
--   total_orders, total_revenue, avg_order_value
--
-- revenue_by_customer columns:
--   customer_id, customer_name, customer_segment,
--   total_orders, total_revenue, avg_order_value, lifetime_value_actual
--
-- customer_segmentation columns:
--   segment_type, customer_count, avg_revenue, total_revenue
