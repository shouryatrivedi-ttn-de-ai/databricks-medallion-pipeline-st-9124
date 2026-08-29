# Reflection

## Project Overview

I built an end-to-end Databricks Medallion pipeline for e-commerce analytics. Three operational CSV sources (customers, orders, products) must flow into trusted analytics without assuming the source data is clean. The sample dataset includes roughly 700 intentional defects - NULL emails, duplicate keys, orphan foreign keys - so the pipeline detects and measures quality problems rather than hiding them.

The flow is Bronze -> Silver -> Gold -> Databricks SQL Dashboard. Bronze preserves raw Delta tables. Silver flags invalid rows. Gold aggregates eligible records. A SQL dashboard exposes product, customer, and segmentation insights. I used AI-assisted development throughout, but the implementation, debugging, and trade-offs are grounded in repository code, validation scripts, git history, and `ai-prompts/`.

## What I Built

**Sample data.** A reproducible Python generator (seed 42) produces 10K customers, 100K orders, and 500 products with intentional defects and self-validates defect counts.

**Bronze.** I ingested CSVs into `workspace.bronze` Delta tables with explicit schemas, `FAILFAST` reading, ingestion metadata, and `ingestion_log`. Validation confirms row counts (500 / 10K / 100K) and metadata. Bronze was executed on Databricks against a Unity Catalog Volume.

**Silver.** Four active checks: completeness, uniqueness, type/domain validation, and referential integrity. Silver adds `quality_check_result`, `quality_failure_reasons`, and `_silver_processed_at` while retaining 100% of Bronze rows. `quality_metrics` reports pass rates. `validate_silver.py` verifies retention and intentional defect flagging. `05_quality_business_logic.py` exists as a stub and is not wired in.

**Gold.** Three tables in `workspace.gold`:

- `sales_by_product` - eligible order/product sales metrics
- `revenue_by_customer` - per-customer revenue and `lifetime_value_actual`
- `customer_segmentation` - High-Value, Repeat, One-Time, Inactive segments

Eligibility is defined in `eligibility.py` via granular failure codes. SQL files perform aggregations. `validate_gold.py` checks metrics and cross-table revenue consistency.

**Dashboard.** Four Databricks SQL visualizations: Customer Distribution by Segment, Total Revenue by Customer Segment, Top 10 Customers by Revenue, and Total Revenue by Product Category. `dashboard_queries.sql` and `DASHBOARD_GUIDE.md` document QUERY 1-4, parameters, and filters.

## Key Technical Decisions

**Flag, don't delete.** Silver retains every Bronze row with quality flags. That supports auditing, defect measurement, and downstream eligibility decisions. Deleting bad rows would have hidden the intentional test defects and made validation harder.

**Modular checks.** Separate modules per check type produce independent metrics and standardized failure codes (`COMPLETENESS_EMAIL`, `RI_CUSTOMER`, etc.). This made reporting and extension straightforward.

**Granular Gold eligibility.** Not every Silver `FAIL` row is excluded from every metric. For example, NULL email does not exclude a customer from revenue aggregation; duplicate `customer_id` does. Gold filters completed orders and entity-specific critical codes rather than using blanket PASS-only logic.

**PySpark orchestration, SQL aggregations.** Bronze and Silver are pipeline-oriented PySpark jobs with shared utilities. Gold business logic is set-oriented and reads clearly in SQL, which also maps well to dashboard queries.

## Challenges and Debugging

**Silver uniqueness on Databricks.** Filtering directly on a window function caused `WINDOW_FUNCTION_NOT_ALLOWED_IN_CLAUSE`. I materialized `_duplicate_count`, filtered on that column, and dropped it before write (commit `720ffee`).

**Gold validation baselines.** Validation failed after a correct Gold run because customer-level totals were compared against all eligible orders, while Gold SQL uses customer-attributed populations. I fixed `validate_gold.py` only and added a revenue consistency check between `revenue_by_customer` and `customer_segmentation` (commit `68b8bc9`).

**Unity Catalog and Volume paths.** Three-part table names (`workspace.bronze.*`) and Volume CSV paths required config changes and a `resolve_csv_path()` branch without local `Path.exists()`. Databricks execution used `sys.path` imports from the Git repo, not `%run` on `.py` files.

**Dashboard alignment.** Initial SQL targeted assignment-style charts (histogram, top products), but the deployed dashboard used four different business tiles. I aligned queries, guide, and README to the deployed layout (commits `f3d8519`, `ae8922d`).

**Git workflow.** Work proceeded on feature branches per layer with PR merges (`feature/bronze-layer`, `feature/silver-layer`, `feature/gold-layer` into `master`). Syncing the Databricks Git folder after each push was a recurring practical step.

## What I Learned

Medallion architecture is more than three schemas. Each layer needs explicit contracts: what stays raw, what gets flagged, what is eligible for which metric, and how that is validated.

Data quality design shapes analytics. Flagging vs deleting and granular Gold eligibility directly affect revenue and segment numbers stakeholders see.

Validation scripts at each layer (`validate_bronze.py`, `validate_silver.py`, `validate_gold.py`) provide repeatable checks and helped surface issues during implementation. `ingestion_log` and `quality_metrics` add basic observability.

Git discipline - feature branches, PRs, and documented troubleshooting - is part of delivering data pipelines, not an optional software-engineering extra.

Documentation and honest gap reporting (stubs, missing pytest suite) are part of maintainability.

## What I Would Improve Next

- Add a formal `tests/` suite with pytest
- Implement and wire business logic validation in Silver
- Automate runs with Databricks jobs/workflows and add CI/CD
- Improve structured logging and persisted validation reports per run
- Add dashboard screenshots and Silver/Gold execution docs similar to Bronze's `ai-prompts/07`

## Final Takeaway

A credible Medallion pipeline is defined by decisions at each boundary: what raw means, what "bad data" means, which failures block which metrics, and how you prove the system behaved correctly. The platform is Databricks; the engineering is in those boundaries and in making them reproducible for the next person who runs the pipeline.
