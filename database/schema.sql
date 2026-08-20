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
