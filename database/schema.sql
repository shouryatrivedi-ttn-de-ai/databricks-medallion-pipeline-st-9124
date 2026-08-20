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
