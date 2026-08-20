# AI Prompt 05 — Bronze Layer Implementation

## Purpose / Context

With sample CSVs generated and validated, the next phase was Bronze-layer ingestion: read the three source files into Delta tables without cleaning or transforming business data.

Bronze must preserve intentional NULLs, duplicates, orphan foreign keys, and other defects for Silver validation later.

## Prompt Sent

We have finished generating and validating the source CSV files. I want to implement the Bronze layer next.

Based on the existing project structure and design documents, create the Bronze ingestion code under `src/bronze/`.

The Bronze layer should read the three generated CSV files and write them as Delta tables for customers, orders and products.

Keep the source data unchanged. Do not clean, deduplicate, reject or apply business validation to the records.

Add only ingestion metadata that is useful for traceability, such as source file name and ingestion timestamp.

Use explicit schemas where practical, especially because the source intentionally contains NULLs and invalid values that we need to preserve for Silver validation.

Keep the implementation modular and suitable for running as a Databricks PySpark job later.

Do not implement Silver, Gold or dashboard logic.

Also add a simple validation approach for Bronze that checks expected row counts and confirms the ingestion metadata exists.

After making the changes, explain the files created, how the Bronze flow works, and any assumptions you made.

## AI Response Summary

Cursor implemented a modular Bronze ingestion layer under `src/bronze/` plus shared config in `src/config.py` and schema setup in `database/schema.sql`.

### Files created

| File | Purpose |
|------|---------|
| `src/config.py` | `DATA_PATH`, `BRONZE_SCHEMA`, expected row counts |
| `src/bronze/schemas.py` | Explicit Spark schemas for customers, orders, products |
| `src/bronze/ingest_utils.py` | Shared read/write/log logic |
| `src/bronze/validate_bronze.py` | Row count and metadata validation |
| `src/bronze/01_ingest_customers.py` | Single-table ingest job |
| `src/bronze/02_ingest_orders.py` | Single-table ingest job |
| `src/bronze/03_ingest_products.py` | Single-table ingest job |
| `src/bronze/ingest_all.py` | Orchestrator + validation |
| `database/schema.sql` | `CREATE SCHEMA IF NOT EXISTS bronze` |

## Key Decisions / Outcomes

### Bronze flow

```
CSV (data/)
  → read with explicit schema
  → add _ingest_timestamp, _source_file
  → write Delta table (overwrite)
  → append row to bronze.ingestion_log
  → validate row counts + metadata
```

### Explicit schemas

Spark schemas were defined in `schemas.py` for all three entities, with nullable columns where the source intentionally contains NULLs (for example nullable FK columns on orders).

### Ingestion metadata

Each Bronze entity table includes:

- `_ingest_timestamp` — when the row was ingested
- `_source_file` — source CSV filename

### Audit log

`bronze.ingestion_log` records:

- `entity`
- `row_count`
- `ingest_timestamp`
- `source_path`

### Orchestrator

`ingest_all.py` ingests in order: **products → customers → orders**, then runs Bronze validation.

Individual per-table scripts (`01_`, `02_`, `03_`) can also be run separately as Databricks jobs.

### Bronze validation

`validate_bronze.py` checks:

- Expected row counts (10,000 / 100,000 / 500)
- `_ingest_timestamp` and `_source_file` columns exist and are populated
- `bronze.ingestion_log` contains entries for all three entities

### Bronze non-goals (preserved by design)

Bronze does **not**:

- deduplicate primary keys
- impute NULLs
- reject orphan foreign keys
- apply business validation or cleaning

Intentional defects from the sample data generator are preserved for Silver.

## Assumptions Documented at Implementation Time

- **Write mode:** `overwrite` per full pipeline run (acceptable for this exercise).
- **DATA_PATH:** defaults to repo `data/` locally; override via environment variable on Databricks (for example `/dbfs/FileStore/medallion/data/`).
- **Nullable PK/FK columns:** Bronze schemas use nullable types where needed so NULLs and duplicate keys are not rejected at ingest.
- **ingestion_log:** append-only audit trail; table is created on first ingest.

## What I Accepted

- Modular Bronze structure with shared utilities and per-table entry points.
- Explicit Spark schemas in a dedicated module.
- Ingestion metadata columns and `bronze.ingestion_log`.
- Bronze validation for row counts and metadata presence.
- Orchestrator script with products-first ingest order.
- Principle that Bronze is raw ingest only — no cleaning.

## What I Changed

No major structural changes during the initial Bronze implementation. A follow-up review iteration addressed the CSV read/cast approach (documented in `06-bronze-layer-review-and-improvements.md`).

## What I Rejected

- Any cleaning, deduplication, or rejection of bad records at Bronze.
- Implementing Silver, Gold, or dashboard logic in the same step.

## Why

Bronze must mirror source data faithfully so Silver can detect and flag known intentional defects. Metadata and audit logging add traceability without altering business values.

## Validation

- Bronze code structure reviewed against assignment repository layout and design notes.
- Expected row counts aligned with validated sample data volumes.
- Validation module defined checks for row counts, metadata columns, and ingestion log entries.
