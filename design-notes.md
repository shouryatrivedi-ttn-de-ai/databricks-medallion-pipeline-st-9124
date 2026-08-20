# Design Notes

> **Status:** Technical design for review (pre-implementation).  
> **Spec:** `docs/assignment.md` | **Requirements:** `requirements-analysis.md`

## Architecture Overview

Simple Medallion pipeline on **Databricks Community Edition** using **Python**, **PySpark**, **SQL**, and **Delta Lake** tables. No additional orchestration, streaming, or external services beyond what the assignment requires.

```
CSV files (data/)
      │
      ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────────────┐
│   Bronze    │───▶│   Silver    │───▶│    Gold     │───▶│ SQL Dashboard    │
│  raw ingest │    │ 4 DQ checks │    │ 3 agg tables│    │ 3+ visualizations│
│  unchanged  │    │ flag rows   │    │ agg-eligible│    │                  │
└─────────────┘    └─────────────┘    └─────────────┘    └──────────────────┘
                          │
                          ▼
                   quality_metrics
                   (cross-cutting report)
```

### Design principles

| Principle | Application |
|-----------|-------------|
| Bronze = raw | No cleaning, deduplication, or FK enforcement |
| Silver = flag, don't delete | Every input row appears in Silver output |
| Gold = business-ready | Reads Silver using **aggregation-specific eligibility**—not a blanket exclude on every `FAIL` *(WD-07)* |
| Explicit schemas | Silver and Gold use defined schemas, not inference |
| Modular scripts | One responsibility per file, matching repo structure |
| Config over hardcoding | Paths and table names in a shared config module |

### Technology stack (minimal)

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Compute | Databricks cluster (Community Edition) | Assignment target platform |
| Storage | Delta Lake tables in Hive metastore | Native Databricks pattern; supports SQL dashboard |
| Data generation | Python + pandas + Faker (local) | Fast iteration; writes CSVs to `data/` |
| Ingest / Silver | PySpark notebooks or `.py` jobs | Assignment requirement |
| Gold / Dashboard | Spark SQL / Databricks SQL | Assignment requirement |
| Tests | pytest + PySpark (local or cluster) | One meaningful test tier minimum |

---

## End-to-End Pipeline Flow

### Step 1: Generate CSVs (local or Databricks)

`src/data_generation/generate_sample_data.py` writes three files to `data/` with intentional quality defects, then copies/uploads to DBFS for ingest.

### Step 2: Bronze ingest

Read CSVs from DBFS → write Delta tables under `bronze` schema. Log row counts.

### Step 3: Silver validation

Read Bronze → apply four core quality checks → write flagged Silver tables + `silver.quality_metrics`.

### Step 4: Gold aggregation

Read Silver (aggregation-eligible rows + Completed orders) → write three Gold Delta tables via SQL.

### Step 5: Dashboard

Run SQL queries against Gold tables in Databricks SQL Dashboard UI.

---

## Sample Data Generation

### Approach

| Aspect | Design |
|--------|--------|
| Library | Python, pandas, Faker |
| Output | `data/customers.csv`, `data/orders.csv`, `data/products.csv` |
| Volumes | 10,000 / 100,000 / 500 rows |
| Reproducibility | Fixed random seed; post-generation count assertions |

### Generation order

1. **Products** — clean PKs; FK domain for orders.
2. **Customers** — base generation, then inject NULL emails (50) and duplicate `customer_id` (10 keys).
3. **Orders** — sample valid FKs from parents, then inject NULL FKs, orphan FKs, duplicate `order_id` (20 keys).

### Intentional defects (assignment requirement)

| File | Defect | Count |
|------|--------|-------|
| customers | NULL `email` | 50 |
| customers | Duplicate `customer_id` | 10 |
| orders | NULL `customer_id` | 100 |
| orders | NULL `product_id` | 200 |
| orders | Orphan `customer_id` | 50 |
| orders | Orphan `product_id` | 30 |
| orders | Duplicate `order_id` | 20 |

**Assumption:** Type/schema validation will not have dedicated intentional defects in v1 unless we add a small number during generation (e.g., invalid `order_status` values). Core tests focus on completeness, uniqueness, and RI defects above.

### Documentation

`DATA_GENERATION_NOTES.md` records seed, counts, and any deviations from the ~700 problematic-row target.

---

## Bronze Layer

### Tables

| Table | Source CSV | Write mode |
|-------|------------|------------|
| `bronze.products` | `products.csv` | Overwrite per full pipeline run *(assumption)* |
| `bronze.customers` | `customers.csv` | Overwrite |
| `bronze.orders` | `orders.csv` | Overwrite |

**Assumption:** Overwrite mode is acceptable for this exercise (single batch). Production would use append + batch ID.

### Per-table ingest (`01_ingest_*.py`)

1. Read `DATA_PATH` from config (default: `/dbfs/FileStore/medallion/data/`).
2. Read CSV with explicit schema matching `data-model.md`.
3. Add metadata: `_ingest_timestamp`, `_source_file`.
4. Write to `bronze.<entity>` as Delta.
5. Print and optionally persist row count to `bronze.ingestion_log`.

### Orchestrator (`ingest_all.py`)

Run products → customers → orders. Abort if any source file is missing or empty.

### Bronze non-goals

No deduplication, NULL imputation, type coercion beyond read, FK checks, or column renaming.

---

## Silver Layer

### Four core quality validations (working decision WD-01)

The assignment requires four checks but names only three. Our fourth core check is **type/schema validation**—an interpretation, not an explicit assignment mandate. See `requirements-analysis.md`.

| # | Check | Module | Required |
|---|-------|--------|----------|
| 1 | Completeness | `01_quality_completeness.py` | Core |
| 2 | Uniqueness | `02_quality_uniqueness.py` | Core |
| 3 | Type/schema validation | `03_quality_type_validation.py` | Core *(interpretation)* |
| 4 | Referential integrity | `04_quality_referential_integrity.py` | Core |
| — | Business-rule validation | `05_quality_business_logic.py` | Optional/stretch |
| — | Quality metrics report | Part of `create_silver_tables.py` | Cross-cutting output |

### Processing flow

```
bronze.products ──▶ silver.products ──┐
bronze.customers ─▶ silver.customers ─┼──▶ (RI uses silver parents)
bronze.orders ────▶ silver.orders ────┘
                           │
                           ▼
                  silver.quality_metrics
```

**Orchestrator (`create_silver_tables.py`):**

1. Build `silver.products` and `silver.customers` first (parent tables).
2. Build `silver.orders` (child table; RI joins to Silver parents).
3. Each entity script runs checks in order: completeness → uniqueness → type → RI.
4. Merge failure codes into flag columns.
5. Write `silver.quality_metrics` summarizing pass/fail counts per check.

### How bad records are retained (assignment requirement)

Silver tables contain **100% of Bronze rows**. No `filter(...).drop()` on failed records.

**Mechanism:**

1. Start with all Bronze columns copied forward.
2. Initialize `quality_check_result = 'PASS'` and `quality_failure_reasons = NULL`.
3. Each check module returns failure flags per row (boolean or failure code).
4. Orchestrator combines flags:
   - Any failure → `quality_check_result = 'FAIL'`
   - Append codes to `quality_failure_reasons` (pipe-separated, e.g. `COMPLETENESS|UNIQUENESS`)
5. Write the full dataset to `silver.<entity>`.

Failed rows remain queryable for audit, debugging, and quality reporting. Gold layers apply **aggregation-specific eligibility rules** (see below)—a Silver `FAIL` does not automatically exclude a record from every downstream use case.

### Silver-to-Gold eligibility model

Silver `quality_check_result = 'FAIL'` means **at least one check failed**. That is the correct overall audit signal and drives the quality metrics report. Gold, however, applies **per-aggregation criticality rules**: only failures that invalidate a record's role in a specific aggregation exclude it from that aggregation.

#### Critical vs non-critical failures

| Category | Meaning | Gold behavior |
|----------|---------|---------------|
| **Critical** | The failure makes the record unsafe or meaningless for a specific aggregation | Exclude from that aggregation's inputs |
| **Non-critical** | The record is flagged for reporting but remaining fields are usable | May still participate in aggregations that do not depend on the failed field |

#### Failure criticality by entity

**orders** — used as fact rows in revenue/order metrics:

| Failure code | Critical for order-based metrics? | Rationale |
|--------------|-------------------------------------|-----------|
| `COMPLETENESS` | **Yes** | Missing `customer_id` or `product_id` breaks joins and attribution |
| `UNIQUENESS` | **Yes** | Duplicate `order_id` risks double-counting revenue |
| `RI_CUSTOMER` | **Yes** | Orphan customer link; revenue cannot be attributed reliably |
| `RI_PRODUCT` | **Yes** | Orphan product link; product sales attribution invalid |
| `TYPE_VALIDATION` | **Yes** *(key fields)* | Invalid `order_id`, `customer_id`, `product_id`, `total_amount`, `order_status`, or `order_date` breaks aggregation |
| `TYPE_VALIDATION` | No *(non-key fields)* | e.g. invalid `payment_date` when Gold does not use it *(assumption)* |

**customers** — used as dimension in segmentation and revenue-by-customer:

| Failure code | Critical for customer aggregations? | Rationale |
|--------------|-------------------------------------|-----------|
| `UNIQUENESS` | **Yes** | Duplicate `customer_id` makes the dimension ambiguous |
| `COMPLETENESS` (`email`) | **No** | Missing email is flagged but customer can still be segmented and attributed revenue |
| `TYPE_VALIDATION` | **Yes** *(key fields)* | Invalid `customer_id` breaks joins |
| `TYPE_VALIDATION` | No *(non-key fields)* | e.g. invalid `lifetime_value` or `signup_date` when not used in Gold *(assumption)* |

**products** — used as dimension in sales-by-product:

| Failure code | Critical for product aggregations? | Rationale |
|--------------|-----------------------------------|-----------|
| `UNIQUENESS` | **Yes** | Duplicate `product_id` makes the dimension ambiguous |
| `COMPLETENESS` (`product_id`, `product_name`) | **Yes** | Cannot attribute sales without identity |
| `TYPE_VALIDATION` | **Yes** *(key fields)* | Invalid `product_id` breaks joins |
| `TYPE_VALIDATION` | No *(non-key fields)* | e.g. invalid `stock_quantity` when not used in Gold *(assumption)* |

#### Gold helper views (conceptual)

Gold SQL will use eligibility filters rather than `quality_check_result = 'PASS'` alone:

```
aggregation_eligible_orders =
  silver.orders
  WHERE order_status = 'Completed'   -- WD-11
    AND NOT has_critical_order_failure(...)

segmentation_eligible_customers =
  silver.customers
  WHERE NOT has_critical_customer_failure_for_segmentation(...)
    -- UNIQUENESS only; email NULL does NOT exclude

revenue_eligible_customers =
  segmentation_eligible_customers
  WITH at least one aggregation_eligible_order

product_eligible_products =
  silver.products
  WHERE NOT has_critical_product_failure(...)
```

**Assumption (WD-07, revised):** Criticality is defined per entity and per Gold table, not as a global PASS-only gate.

### Check 1: Completeness

**Assignment fields:** `email`, `customer_id`, `product_id`

| Table | Fields checked | Failure code |
|-------|----------------|--------------|
| `customers` | `email IS NULL` | `COMPLETENESS` |
| `orders` | `customer_id IS NULL`, `product_id IS NULL` | `COMPLETENESS` |
| `products` | `product_id IS NULL`, `product_name IS NULL` | `COMPLETENESS` |

**Assumption (WD-04):** Completeness on `customer_id`/`product_id` applies to **orders**, not the customers/products PK tables (no intentional NULL PKs injected).

**Overlap rule:** NULL FK on orders fails completeness; RI is skipped for that field *(NULL FK is not evaluated for orphan lookup)*.

### Check 2: Uniqueness

**Assignment:** duplicate `order_id`, `customer_id`

| Table | Key | Failure code |
|-------|-----|--------------|
| `customers` | `customer_id` | `UNIQUENESS` |
| `orders` | `order_id` | `UNIQUENESS` |
| `products` | `product_id` | `UNIQUENESS` |

**Assumption (WD-05):** Uniqueness on `customer_id` applies to the **customers** table only. Multiple orders per customer is valid.

**Flagging rule:** All rows participating in a duplicate key group are flagged (not just the "second" row).

### Check 3: Type/schema validation (working interpretation)

Validates that values conform to expected types and allowed enums after Bronze ingest.

| Table | Rules | Failure code |
|-------|-------|--------------|
| `customers` | `customer_id` castable to INT; `signup_date` valid DATE; `customer_segment IN ('Premium','Standard','Basic')`; `lifetime_value` numeric | `TYPE_VALIDATION` |
| `orders` | IDs and quantities castable to INT; dates valid; `order_status IN ('Pending','Completed','Cancelled')`; monetary fields numeric | `TYPE_VALIDATION` |
| `products` | IDs and stock fields castable to INT; monetary fields numeric | `TYPE_VALIDATION` |

**Implementation approach:** Apply explicit casts with safe parsing; rows where cast fails or enum not in allowed set get flagged. Bronze may store everything as string initially—Silver enforces typed columns plus flags.

**Assumption:** No intentional type defects in v1 sample data; this check validates schema conformance on clean generated data and catches drift if introduced later.

### Check 4: Referential integrity

**Assignment:** every `customer_id` and `product_id` on orders must exist in parent tables.

| Child | FK | Parent | Condition | Failure code |
|-------|-----|--------|-----------|--------------|
| `orders` | `customer_id` | `silver.customers` | FK IS NOT NULL AND no match | `RI_CUSTOMER` |
| `orders` | `product_id` | `silver.products` | FK IS NOT NULL AND no match | `RI_PRODUCT` |

**Assumption (WD-06):** RI runs on orders only. Parent tables are reference dimensions.

**Note:** Use `silver.customers` / `silver.products` as reference (not Bronze) so parent-side quality state is consistent.

### Optional: Business-rule validation (stretch)

Not required for core completion (WD-03). If implemented:

- `total_amount ≈ quantity * unit_price` (tolerance 0.01)
- `order_status = 'Completed' AND payment_date IS NULL` → flag

Failure code: `BUSINESS_LOGIC`.

### Quality metrics report (cross-cutting)

Written by `create_silver_tables.py` to `silver.quality_metrics`:

| Column | Description |
|--------|-------------|
| `run_timestamp` | When checks ran |
| `entity` | customers / orders / products |
| `check_name` | completeness / uniqueness / type_validation / ri_customer / ri_product |
| `total_rows` | Rows evaluated |
| `failed_rows` | Rows where this check failed |
| `passed_rows` | `total_rows - failed_rows` |
| `pass_pct` | `(passed_rows / total_rows) * 100` |

Also print a summary table to stdout for README verification steps.

**Assumption:** Delta table format for the report (spec does not mandate format).

### Silver products scope

**Assumption:** Products receive the same four checks (completeness, uniqueness, type, no RI) even though the assignment defines no intentional product defects. This keeps the pipeline symmetric and supports future test data.

---

## Gold Layer

Gold reads from **Silver tables** using the **aggregation-specific eligibility model** above—not a blanket `quality_check_result = 'PASS'` filter.

**Assignment gap:** Order status treatment is not specified. We exclude `Cancelled` and `Pending` from revenue and order counts *(assumption WD-11)*. Document in README.

### Shared order base (aggregation-eligible orders)

Order-based metrics use only **aggregation-eligible orders**:

```
aggregation_eligible_orders =
  silver.orders
  WHERE order_status = 'Completed'
    AND no critical order failure
    -- excludes: COMPLETENESS, UNIQUENESS, RI_CUSTOMER, RI_PRODUCT,
    --           TYPE_VALIDATION on key metric/join fields
```

Parent dimensions (`customers`, `products`) use their own eligibility rules per aggregation below.

---

### Aggregation 1: Sales by Product

**Output table:** `gold.sales_by_product`  
**Script:** `01_sales_by_product.sql`

| Column | Source / calculation |
|--------|---------------------|
| `product_id` | `products.product_id` |
| `product_name` | `products.product_name` |
| `category` | `products.category` |
| `total_orders` | `COUNT(DISTINCT order_id)` from aggregation-eligible orders |
| `total_revenue` | `SUM(total_amount)` |
| `avg_order_value` | `total_revenue / total_orders` |

Join `aggregation_eligible_orders` to **product-eligible** `silver.products` (excludes duplicate `product_id`, missing name/id; non-key type failures may still qualify).

**Assumption:** Inner join—products with zero aggregation-eligible orders are omitted. Acceptable for "Top 10 products by revenue" dashboard use case.

---

### Aggregation 2: Revenue by Customer

**Output table:** `gold.revenue_by_customer`  
**Script:** `02_revenue_by_customer.sql`

| Column | Source / calculation |
|--------|---------------------|
| `customer_id` | `customers.customer_id` |
| `customer_name` | `customers.customer_name` |
| `customer_segment` | `customers.customer_segment` (source tier: Premium/Standard/Basic) |
| `total_orders` | Count of aggregation-eligible orders per customer |
| `total_revenue` | `SUM(total_amount)` |
| `avg_order_value` | `total_revenue / total_orders` |
| `lifetime_value_actual` | `SUM(total_amount)` over aggregation-eligible orders |

**Assumption (WD-08):** `lifetime_value_actual` = computed revenue from orders, **not** the source `customers.lifetime_value` field.

**Population rule:** **Inner join** — only **revenue-eligible customers** appear (segmentation-eligible customer with ≥ 1 aggregation-eligible order). Customers with zero eligible orders are excluded here but **included in segmentation as Inactive** via the LEFT JOIN pattern below.

**Non-critical example:** A customer with NULL `email` (`COMPLETENESS` failure) but valid `customer_id` and eligible orders **can appear** in this table.

---

### Aggregation 3: Customer Segmentation

**Output table:** `gold.customer_segmentation`  
**Script:** `04_customer_segmentation.sql`

**Assignment provides segment labels only** — no business rules. Thresholds below are **design assumptions (WD-09)**, not assignment requirements.

Segmentation **must retain Inactive customers** (zero eligible orders). Build customer order metrics with a **customers-first LEFT JOIN**, not an orders-first inner join.

#### Step 1: Aggregate order metrics (order grain)

```
customer_order_metrics =
  aggregation_eligible_orders
  GROUP BY customer_id
  → total_orders = COUNT(DISTINCT order_id)
  → total_revenue = SUM(total_amount)
```

#### Step 2: Start from customers; LEFT JOIN metrics

```
segmentation_base =
  segmentation_eligible_customers c          -- from silver.customers;
  LEFT JOIN customer_order_metrics m         -- critical customer failures only (UNIQUENESS)
    ON c.customer_id = m.customer_id
  SELECT
    c.customer_id,
    COALESCE(m.total_orders, 0)  AS total_orders,
    COALESCE(m.total_revenue, 0) AS total_revenue
```

**Why LEFT JOIN:** Customers with no aggregation-eligible orders remain in `segmentation_base` with `total_orders = 0` and `total_revenue = 0`, enabling **Inactive** classification. An inner join from orders would drop them entirely.

**Non-critical example:** Customers with NULL `email` remain segmentation-eligible and appear in the appropriate segment based on their eligible order history (or Inactive if none).

#### Step 3: Assign segment (mutually exclusive, priority order)

| Priority | segment_type | Rule *(assumption)* |
|----------|--------------|---------------------|
| 1 | **High-Value** | `total_revenue >= 1000` |
| 2 | **Repeat** | `total_orders >= 2` (and not High-Value) |
| 3 | **One-Time** | `total_orders = 1` |
| 4 | **Inactive** | `total_orders = 0` |

**Assumptions:**
- Threshold `$1000` unchanged from prior design.
- Segments use **aggregation-eligible completed orders** only for metrics.
- Every **segmentation-eligible** customer appears in exactly one segment (includes Inactive).
- Customers with critical `UNIQUENESS` failure are excluded from segmentation entirely (ambiguous identity).

#### Step 4: Aggregate to segment grain

| Column | Calculation |
|--------|-------------|
| `segment_type` | High-Value / Repeat / One-Time / Inactive |
| `customer_count` | `COUNT(*)` |
| `avg_revenue` | `AVG(total_revenue)` per customer, then averaged at segment level |
| `total_revenue` | `SUM(total_revenue)` across customers in segment |

---

### Optional: Daily/weekly trends

`03_daily_weekly_trends.sql` — **optional/stretch (WD-10)**. Not required for core acceptance. Omit from initial implementation unless time permits.

### Gold orchestration

`create_gold_tables.py` runs SQL files 01, 02, 04 in order. Verify tables exist and row counts are sensible. Log output.

---

## Dashboard

**Platform:** Databricks SQL Dashboard (Community Edition)

### Required tiles (assignment)

| Tile | Gold source | Chart | Query outline |
|------|-------------|-------|---------------|
| Top 10 products by revenue | `gold.sales_by_product` | Bar | `ORDER BY total_revenue DESC LIMIT 10` |
| Customer revenue distribution | `gold.revenue_by_customer` | Histogram | Bucket `total_revenue` into ranges |
| Customer segmentation | `gold.customer_segmentation` | Pie | `segment_type`, `customer_count` |

**Assumption:** Three tiles satisfy "3+ tiles" minimum. A fourth tile (e.g., KPI summary) is optional.

### Filters *(recommended, not required)*

- Product `category`
- Customer `customer_segment` (Premium/Standard/Basic)

### Artifacts

- `src/dashboard/dashboard_queries.sql`
- `src/dashboard/DASHBOARD_GUIDE.md` — UI setup steps

---

## Testing Approach

Practical, layered testing focused on proving the pipeline works and quality checks catch intentional defects.

### Tier 1: Data generation validation (pre-pipeline)

Run after `generate_sample_data.py`:

- Assert row counts: 10K / 100K / 500.
- Assert defect counts match assignment (NULL emails = 50, etc.).
- Fast; runs locally without Databricks.

### Tier 2: Silver data quality tests (primary)

Run against full or sample dataset on Databricks (or local PySpark):

| Test | Assertion |
|------|-----------|
| Completeness — email | ≥ 50 customers flagged with `COMPLETENESS` |
| Completeness — order FKs | ≥ 100 NULL `customer_id`; ≥ 200 NULL `product_id` flagged |
| Uniqueness — customers | ≥ 10 duplicate `customer_id` groups flagged |
| Uniqueness — orders | ≥ 20 duplicate `order_id` groups flagged |
| RI — customer | ≥ 50 orphan `customer_id` flagged with `RI_CUSTOMER` |
| RI — product | ≥ 30 orphan `product_id` flagged with `RI_PRODUCT` |
| Row retention | `count(bronze.orders) == count(silver.orders)` |
| Pass rate report | `silver.quality_metrics` has one row per check; pass_pct < 100 where defects exist |

### Tier 3: Pipeline smoke tests

| Test | Assertion |
|------|-----------|
| Bronze ingest | Bronze row counts match CSV line counts (minus header) |
| Gold tables exist | All three Gold tables created with > 0 rows |
| Gold filter | No Silver FAIL rows in revenue totals | Verify aggregation-eligible logic excludes critical failures only |
| Segmentation — Inactive | `Inactive` segment has `customer_count > 0` | Customers with zero eligible orders present via LEFT JOIN |
| Segmentation — coverage | Sum of segment `customer_count` = segmentation-eligible customers | All non-duplicate customers classified |

### Tier 4: Gold correctness (spot checks)

Hand-compute on a small known subset:

- Pick one product → verify `total_revenue` and `total_orders`.
- Pick one customer → verify `lifetime_value_actual` equals sum of their aggregation-eligible completed orders.
- Verify segmentation counts sum to segmentation-eligible customer count (not all Silver customers if duplicates exist).
- Confirm at least one customer classified as **Inactive** on generated data *(expected: customers with no completed eligible orders)*.

### Test tooling

| Environment | Tool |
|-------------|------|
| Local | pytest + PySpark (optional for CI-friendly runs) |
| Databricks | Notebook or job with assertion cells |

**Assumption:** `--sample` mode in generator (e.g., 1K orders) for fast dev tests; full dataset for final submission validation.

---

## Error Handling

| Stage | Failure | Behavior |
|-------|---------|----------|
| Data generation | Write error | Exit code 1, log message |
| Bronze | Missing CSV | Abort `ingest_all.py`, log path |
| Bronze | Zero rows | Abort with warning |
| Silver | Empty Bronze table | Fail with explicit error |
| Silver | Cast failure in type check | Flag row as FAIL, continue processing |
| Gold | No qualifying orders | Create Gold tables (may be empty); log warning |
| Config | Invalid path | Fail at startup with clear message |

Use Python `logging` throughout. Capture issues in `debugging-notes.md` during development.

### Configuration module

Centralize in `src/config.py` (or similar):

- `DATA_PATH`, `BRONZE_SCHEMA`, `SILVER_SCHEMA`, `GOLD_SCHEMA`
- No secrets or credentials in code

---

## Step-by-Step Implementation Order

Recommended build sequence for review and development:

| Phase | Step | Deliverable | Depends on |
|-------|------|-------------|------------|
| **0** | Project scaffold | `database/schema.sql`, `src/config.py`, README skeleton | Design approval |
| **1** | Sample data | `generate_sample_data.py`, CSVs in `data/`, `DATA_GENERATION_NOTES.md` | Phase 0 |
| **1b** | Generation tests | Defect count assertions | Phase 1 |
| **2** | Bronze ingest | `01–03_ingest_*.py`, `ingest_all.py`, `bronze.ingestion_log` | Phase 1 |
| **2b** | Bronze smoke test | Row count validation | Phase 2 |
| **3** | Silver — completeness | `01_quality_completeness.py` | Phase 2 |
| **4** | Silver — uniqueness | `02_quality_uniqueness.py` | Phase 3 |
| **5** | Silver — type validation | `03_quality_type_validation.py` | Phase 4 |
| **6** | Silver — referential integrity | `04_quality_referential_integrity.py` | Phase 2 (parents), 5 |
| **7** | Silver orchestrator | `create_silver_tables.py`, flag columns, `quality_metrics` | Phases 3–6 |
| **7b** | Silver DQ tests | pytest assertions on intentional defects | Phase 7 |
| **8** | Gold aggregations | `01`, `02`, `04` SQL + `create_gold_tables.py` | Phase 7 |
| **8b** | Gold spot-check tests | Revenue/segmentation validation | Phase 8 |
| **9** | Dashboard | `dashboard_queries.sql`, `DASHBOARD_GUIDE.md`, UI setup | Phase 8 |
| **10** | Documentation & artifacts | README end-to-end, prompt history, reflection | All |

**Defer until core complete:** `05_quality_business_logic.py`, `03_daily_weekly_trends.sql`, fourth dashboard tile.

---

## Assumptions Summary

All items below are **design proposals**, not assignment mandates. See `requirements-analysis.md` for full ambiguity list.

| ID | Assumption |
|----|------------|
| WD-01 | Fourth core Silver check = type/schema validation |
| WD-02 | Quality reporting = cross-cutting output |
| WD-03 | Business-rule validation = optional/stretch |
| WD-04 | Completeness scoped per table (email on customers; FKs on orders) |
| WD-05 | Uniqueness on PKs per entity table |
| WD-06 | RI on orders → customers, products |
| WD-07 | Gold uses **aggregation-specific eligibility**—critical failures block participation in a given aggregation; non-critical failures (e.g. NULL email on customers) do not globally exclude records |
| WD-08 | `lifetime_value_actual` = sum of aggregation-eligible completed order revenue |
| WD-09 | Segmentation thresholds unchanged: $1000 / 2+ orders / 1 order / 0 orders; **customers-first LEFT JOIN** retains zero-order Inactive customers |
| WD-10 | Daily/weekly trends = optional/stretch |
| WD-11 | Revenue metrics exclude Cancelled and Pending orders |
| D-01 | Delta overwrite per run (exercise scope) |
| D-02 | Products get full Silver checks despite no intentional defects |
| D-03 | Quality metrics stored as Delta table |
| D-04 | Inner join for sales-by-product (products with sales only) |

---

## Key Trade-offs

| Decision | Choice | Why |
|----------|--------|-----|
| Flag vs delete | Flag all bad rows | Assignment requirement |
| Fourth check | Type/schema validation | Best fit for repo + "four checks" + three named categories |
| Gold input | Aggregation-specific critical failures + Completed orders | Non-blanket PASS filter; NULL email customers can still appear in Gold |
| Segmentation join | Customers LEFT JOIN order metrics | Preserves Inactive customers with zero eligible orders |
| Generator | pandas + Faker locally | Simple; no cluster needed for data prep |
| Overwrite vs append | Overwrite | Simpler for single-batch exercise |
