# Requirement Analysis

> **Source document:** `docs/assignment.md` (also mirrored as `docs/requirements.md` in the repository).

## Problem Statement

An e-commerce company receives daily sales-related data from three operational sources—customer master data, order transactions, and a product catalog—and needs a Databricks-based analytics pipeline that follows the Medallion Architecture (Bronze → Silver → Gold → Dashboard).

The business needs:

1. **Raw ingestion** of CSV files from cloud storage (S3/DBFS) without altering source data.
2. **Validated, queryable Silver tables** where data quality issues are detected, flagged, and measured—not silently removed.
3. **Gold-layer business aggregations** that support revenue, customer, and segmentation analytics.
4. **A BI dashboard** for stakeholders with at least three visualizations backed by SQL queries.

The exercise also requires demonstrating AI-assisted data engineering workflow through planning artifacts, prompt history, testing, and reflection—not only a working pipeline.

## Functional Requirements

### Sample Data Generation

| ID | Requirement |
|----|-------------|
| FR-01 | Provide a Python/PySpark script that generates three CSV files: `customers.csv`, `orders.csv`, `products.csv`. |
| FR-02 | Generate realistic volumes: ~10,000 customers, ~100,000 orders, ~500 products. |
| FR-03 | Intentionally inject the specified quality issues (~700 problematic rows total). |
| FR-04 | Document how data was generated and why quality issues exist (`DATA_GENERATION_NOTES.md`). |
| FR-05 | Commit seed CSVs under `data/`. |

### Bronze Layer

| ID | Requirement |
|----|-------------|
| FR-06 | Ingest all three CSVs from S3/DBFS into Databricks Bronze tables. |
| FR-07 | Preserve raw data unchanged—no cleaning or business transformations. |
| FR-08 | Handle schema inference and appropriate data types. |
| FR-09 | Log ingestion metadata (row counts, timestamp). |
| FR-10 | Provide per-table ingest scripts and an orchestration entry point (`ingest_all.py`). |

### Silver Layer

**What the assignment explicitly states:**

- Implement data quality checks in the Silver layer (acceptance criteria require "all four quality checks").
- The detailed Silver section names three validation categories: **Completeness**, **Uniqueness**, and **Referential Integrity**.
- Flag bad rows via a `quality_check_result` column—do not delete them.
- Generate a quality metrics report showing % passed for each check.
- The repository structure includes five Silver modules: completeness, uniqueness, type_validation, referential_integrity, and business_logic.

**WORKING IMPLEMENTATION DECISION — four core Silver quality validations:**

The assignment does not explicitly name the fourth check. Pending clarification, we will implement these four core validations:

1. **Completeness**
2. **Uniqueness**
3. **Type/schema validation**
4. **Referential integrity**

**Optional / stretch (not mandatory for core completion):**

- **Business-rule validation** (`05_quality_business_logic.py`) — e.g., order amount consistency, payment-date rules.

**Cross-cutting output (not a separate quality check):**

- **Quality metrics/reporting** — aggregates pass/fail outcomes across all checks; produces % passed per check and supports `quality_check_result` flagging.

**Why type/schema validation is selected as the fourth core check:**

- The repository structure explicitly includes `03_quality_type_validation.py`.
- Acceptance criteria require four quality checks working.
- The detailed Silver section explicitly describes only three named validation categories (Completeness, Uniqueness, Referential Integrity).
- Therefore, type/schema validation is the most reasonable interpretation for the fourth core check—not because the assignment explicitly mandates it as one of the four.

| ID | Requirement |
|----|-------------|
| FR-11 | Implement the four core Silver quality validations (see working decision above). |
| FR-12 | **Completeness:** Flag rows with NULLs in critical fields (`email`, `customer_id`, `product_id`). |
| FR-13 | **Uniqueness:** Flag duplicate keys (`order_id`, `customer_id`). |
| FR-14 | **Type/schema validation:** Flag rows with invalid types, unparseable values, or invalid enum values (working interpretation—see ambiguities). |
| FR-15 | **Referential integrity:** Flag orphan foreign keys (`orders.customer_id` → `customers`, `orders.product_id` → `products`). |
| FR-16 | Add a `quality_check_result` (or equivalent) column to flag bad rows—do not delete them. |
| FR-17 | Generate a quality metrics report showing % passed for each check (cross-cutting output of the validation framework). |
| FR-18 | Produce validated Silver tables from Bronze sources. |
| FR-19 | *(Optional/stretch)* **Business-rule validation:** Flag rows violating business rules (e.g., amount consistency)—not required for core completion. |

### Gold Layer

| ID | Requirement |
|----|-------------|
| FR-20 | Create **Sales by Product** aggregation: `product_id`, `product_name`, `category`, `total_orders`, `total_revenue`, `avg_order_value`. |
| FR-21 | Create **Revenue by Customer** aggregation: `customer_id`, `customer_name`, `customer_segment`, `total_orders`, `total_revenue`, `avg_order_value`, `lifetime_value_actual`. |
| FR-22 | Create **Customer Segmentation** aggregation: `segment_type` (High-Value / Repeat / One-Time / Inactive), `customer_count`, `avg_revenue`, `total_revenue`. |
| FR-23 | Aggregation calculations must be correct (sum, count, average, etc.). |

### Dashboard

| ID | Requirement |
|----|-------------|
| FR-24 | Create a Databricks SQL Dashboard with **3+ tiles**. |
| FR-25 | Include visualizations: Top 10 products by revenue (bar), Customer revenue distribution (histogram), Customer segmentation (pie). |
| FR-26 | Provide dashboard SQL queries and setup guide. |
| FR-27 | Support filters where appropriate. |

### Database & Infrastructure

| ID | Requirement |
|----|-------------|
| FR-28 | Provide database schema or setup script (`database/schema.sql`). |
| FR-29 | Provide setup and seed-data notes. |

### Testing, Reporting & Documentation

| ID | Requirement |
|----|-------------|
| FR-30 | Implement input validation and error handling across the pipeline. |
| FR-31 | Implement data quality reporting. |
| FR-32 | Provide at least one meaningful test tier (data quality tests and/or pipeline tests). |
| FR-33 | Provide README with end-to-end setup instructions. |
| FR-34 | Capture full AI prompt history organized by activity. |
| FR-35 | Submit lifecycle artifacts: requirement analysis, design notes, data model, data quality strategy, debugging notes, reflection. |

### Repository Structure

| ID | Requirement |
|----|-------------|
| FR-36 | Follow the prescribed repository layout under `src/`, `data/`, `database/`, `ai-prompts/`, etc. |

## Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-01 | **Readability:** Code must be readable, commented, and documented. |
| NFR-02 | **Maintainability:** Modular structure aligned with Bronze/Silver/Gold separation. |
| NFR-03 | **Testability:** Quality checks must be verifiable against intentional bad data; tests should demonstrate checks catch known issues. |
| NFR-04 | **Traceability:** Bronze data preserved for audit/reprocessing; Silver flags rather than drops invalid records. |
| NFR-05 | **Portability:** Runnable on Databricks Community Edition; CSVs cloneable from repo to DBFS/S3. |
| NFR-06 | **Security:** No hardcoded secrets or credentials in source code. |
| NFR-07 | **Realism:** Intentional quality issue rate (~0.7%) should reflect realistic enterprise data quality expectations. |
| NFR-08 | **AI workflow visibility:** Prompt history, design rationale, and validation evidence are first-class deliverables—not optional extras. |

## Inputs and Outputs

### Inputs

| Input | Format | Location | Description |
|-------|--------|----------|-------------|
| `customers.csv` | CSV | S3/DBFS / `data/` | Customer master: 10K rows, ~500 KB |
| `orders.csv` | CSV | S3/DBFS / `data/` | Order transactions: 100K rows, ~2–3 MB |
| `products.csv` | CSV | S3/DBFS / `data/` | Product catalog: 500 rows, ~50 KB |

### Intermediate Outputs

| Output | Layer | Description |
|--------|-------|-------------|
| `bronze.customers` (or equivalent) | Bronze | Raw customer CSV ingest + ingestion metadata |
| `bronze.orders` | Bronze | Raw order CSV ingest + ingestion metadata |
| `bronze.products` | Bronze | Raw product CSV ingest + ingestion metadata |

### Final Outputs

| Output | Layer | Description |
|--------|-------|-------------|
| `silver.customers` | Silver | Customers with quality flags |
| `silver.orders` | Silver | Orders with quality flags |
| `silver.products` | Silver | Products with quality flags (if in scope) |
| Quality metrics report | Silver | Cross-cutting output: % passed per check (not a separate validation category) |
| `gold.sales_by_product` | Gold | Product-level sales metrics |
| `gold.revenue_by_customer` | Gold | Customer-level revenue metrics |
| `gold.customer_segmentation` | Gold | Segment-level summary metrics |
| Databricks SQL Dashboard | Dashboard | 3+ visualizations with filters |
| Test results | QA | Evidence that intentional issues are detected |

## Acceptance Criteria

Derived from the specification checklist and "What Counts as Complete" section:

- [ ] Sample data generated: 3 CSVs with intentional issues matching specified counts (where unambiguous).
- [ ] Bronze layer ingests all three sources successfully with metadata logging.
- [ ] Silver layer implements all four core quality validations (working interpretation):
  - [ ] **Completeness**
  - [ ] **Uniqueness**
  - [ ] **Type/schema validation**
  - [ ] **Referential integrity**
- [ ] Quality report shows % passed for each check (cross-cutting output—not counted as a fifth check).
- [ ] Gold layer produces all three required aggregation tables with correct math.
- [ ] Dashboard displays all 3+ required visualizations.
- [ ] Code is readable, commented, and documented.
- [ ] README setup instructions work end-to-end on Databricks Community Edition.
- [ ] Data quality tests pass and verify checks catch intentional issues.
- [ ] Full prompt history and lifecycle artifacts are present in the repository.

*(Optional/stretch, not required for core acceptance: business-rule validation module.)*

## Assumptions

### Working implementation decisions

These assumptions resolve spec ambiguities for implementation. They are **our interpretation**, not explicit assignment mandates.

| ID | Assumption |
|----|------------|
| WD-01 | **Four core Silver quality validations:** Completeness, Uniqueness, Type/schema validation, Referential integrity. The assignment requires four checks but names only three; type/schema validation is our chosen fourth check because the repo includes `type_validation` and the detailed Silver section lists three named categories. |
| WD-02 | **Quality metrics/reporting** is a cross-cutting output of the validation framework—not a separate quality check. |
| WD-03 | **Business-rule validation** (`05_quality_business_logic.py`) is optional/stretch—not mandatory for core completion. |
| WD-04 | Completeness applies **per table context**: `email` on customers; `customer_id` and `product_id` on orders (not NULL PK columns on parent tables unless bad data is injected). |
| WD-05 | Uniqueness applies **per entity**: duplicate `customer_id` in `customers`; duplicate `order_id` in `orders`. |
| WD-06 | Referential integrity is evaluated on **orders** referencing `customers` and `products`. |
| WD-07 | Silver "valid" rows for Gold aggregations exclude records failing any core quality check (Gold reads only `quality_check_result = 'PASS'` rows). |
| WD-08 | `lifetime_value_actual` = sum of completed order revenue for the customer—distinct from source `lifetime_value` field which may be stale (spec does not define this field). |
| WD-09 | Customer segmentation rules will be explicitly defined in design (not provided in spec)—see design-notes.md. |
| WD-10 | `gold/03_daily_weekly_trends.sql` is **optional/stretch** since only three Gold aggregations are mandated in the core requirements. |
| WD-11 | Cancelled orders are excluded from revenue aggregations unless otherwise specified (spec silent on order status filtering). |

### General assumptions

| ID | Assumption |
|----|------------|
| A-01 | `docs/assignment.md` is the authoritative specification. |
| A-02 | Storage format for Bronze/Silver/Gold tables will use **Delta Lake** on Databricks (implied by PySpark/Databricks stack, not explicitly mandated). |
| A-03 | Currency/precision: `DECIMAL` types use sufficient precision (e.g., `DECIMAL(18,2)`) for monetary fields. |
| A-04 | Type/schema validation covers castability, valid enums (e.g., `customer_segment`, `order_status`), and parseable dates—but intentional issues in the spec target completeness, uniqueness, and RI; type checks may not have dedicated intentional defects unless added during data generation. |

## Edge Cases

| Edge Case | Consideration |
|-----------|---------------|
| Duplicate `customer_id` with conflicting attribute values | Uniqueness flags all duplicates; downstream must pick a survivorship rule or exclude all duplicates from Gold. |
| Orphan `customer_id` on orders where `customer_id` is non-NULL but not in customers | Referential integrity failure; row flagged in Silver. |
| NULL `customer_id` on orders | Completeness failure; referential integrity check may be N/A or also fail—define explicit behavior. |
| NULL `product_id` on orders | Completeness failure; RI check skipped or fails. |
| Duplicate `order_id` with different column values | Uniqueness flags; revenue could double-count if not excluded from Gold. |
| `total_amount` ≠ `quantity * unit_price` | Not listed as intentional issue; if type/business validation is implemented, define tolerance. |
| `payment_date` NULL while `order_status = Completed` | Nullable by schema; not in mandatory completeness list—potential business-rule edge case. |
| Customer with zero orders | Appears in segmentation as **Inactive**; may be absent from revenue-by-customer Gold table depending on join type. |
| Product with zero orders | May be absent from sales-by-product unless outer join from products. |
| Empty CSV / missing file at ingest | Bronze ingest should fail gracefully with logged error. |
| Schema drift (extra/missing columns) | Bronze preserves raw; Silver should detect via explicit schema or validation. |
| Future `signup_date` | Mentioned in AI prompt example but **not** in mandatory intentional issue list—may or may not appear in generated data. |
| Multiple quality failures on one row | `quality_check_result` should support multiple failure reasons (concatenated codes or array). |

## Ambiguities / Inconsistencies in the Specification

The following conflicts should **not** be silently resolved during implementation without explicit decision.

### 1. Silver quality check count: four vs five vs six

| Source | Statement |
|--------|-----------|
| Common requirements (line ~93) | "Silver layer validation code (**all 4 quality checks** working)" |
| Silver Layer section (lines ~162–167) | Lists **3 named checks** (Completeness, Uniqueness, Referential Integrity) plus flagging/reporting |
| Acceptance criteria (line ~186) | "Silver layer implements **all four quality checks**" |
| Summary (line ~522) | "Implement **four** data quality checks" |
| Repository structure (lines ~215–220) | **Five** silver modules: completeness, uniqueness, **type_validation**, referential_integrity, **business_logic** |
| Submission template for `data-quality-strategy.md` (lines ~321–337) | Documents **3 checks** only (no type validation, no business logic) |

**Impact:** Unclear whether `03_quality_type_validation.py` and `05_quality_business_logic.py` are required deliverables or template placeholders.

**Working resolution (not spec mandate):** Four core checks = Completeness, Uniqueness, Type/schema validation, Referential integrity. Business-rule validation is optional/stretch. Quality reporting is cross-cutting, not a fifth check.

### 2. Uniqueness scope and wording

| Source | Statement |
|--------|-----------|
| Silver Layer (line ~164) | "No duplicate rows (**order_id, customer_id**)" |
| Data quality template (line ~329) | "Check for duplicate **order_id, customer_id**" |
| Intentional issues | 10 duplicate `customer_id` in **customers**; 20 duplicate `order_id` in **orders** |

**Impact:** Wording says "duplicate rows" but issues are **duplicate keys** within each table. Unclear whether `customer_id` uniqueness is also checked on the orders table (would be a different rule: same customer placing multiple orders is valid).

### 3. Completeness field applicability

| Source | Statement |
|--------|-----------|
| Silver Layer (line ~163) | Critical fields: **email, customer_id, product_id** |
| Intentional issues | NULL `email` in customers (50); NULL `customer_id` (100) and NULL `product_id` (200) in **orders** |

**Impact:** `customer_id` completeness on the **customers** table is not an intentional issue. Unclear if completeness runs on all three tables or only fields/table combinations where NULLs are meaningful.

### 4. Gold aggregation count: three vs four SQL files

| Source | Statement |
|--------|-----------|
| Gold Layer section (lines ~169–178) | **Three** aggregation tables (A, B, C) |
| Repository structure (line ~224) | **Four** SQL files including `03_daily_weekly_trends.sql` |
| Dashboard requirements | Three specific visualizations—no "daily/weekly trends" chart listed |

**Impact:** `daily_weekly_trends` may be stretch work or leftover template content.

### 5. Customer segmentation business rules undefined

Gold aggregation C defines segment labels (`High-Value`, `Repeat`, `One-Time`, `Inactive`) but provides **no thresholds or definitions** (e.g., revenue cutoffs, order count rules, time windows).

### 6. `lifetime_value_actual` undefined

Gold aggregation B includes `lifetime_value_actual` alongside source `lifetime_value` with no definition of how "actual" is computed or how it relates to the customer master field.

### 7. Intentional quality issues vs AI prompt example

The AI prompt template example (lines ~384–387) suggests adding **30 rows with `signup_date > today()`** as a quality issue, but the official intentional issues list for customers only specifies NULL email (50) and duplicate customer_id (10).

### 8. Quality thresholds

The submission template for `data-quality-strategy.md` specifies thresholds (>99% complete, 100% unique, >99.9% valid) that are **not** stated in the core Silver Layer requirements or acceptance criteria.

### 9. Silver products table scope

Quality issues are defined for customers and orders only. Unclear whether **products** receive Silver quality treatment or pass through with minimal validation.

### 10. "Flag bad rows" vs separate check modules

Core text describes flagging via `quality_check_result` as part of Silver behavior, while also counting "four quality checks"—unclear whether flagging/reporting is a distinct fourth check or cross-cutting concern.

**Working resolution (not spec mandate):** Quality metrics/reporting and row flagging are treated as cross-cutting outputs. Type/schema validation is treated as the fourth core check. This remains an interpretation—the assignment does not explicitly name the fourth check.

### 11. Dashboard "3+ tiles" vs exactly three visualizations

Requirement says 3+ tiles and lists exactly three chart types. Minimum satisfied at three; whether a fourth tile is expected is ambiguous.

### 12. Primary specification filename

Project brief references `docs/assignment.md`; repository also contains `docs/requirements.md` (content appears equivalent).

### 13. Fourth quality check not explicitly named

The assignment requires "four quality checks" and names three in the detailed Silver section (Completeness, Uniqueness, Referential Integrity). It does **not** explicitly identify the fourth. Our working decision selects type/schema validation; alternative interpretations (e.g., treating reporting as the fourth check) remain plausible until clarified.

## Clarifications that would be useful

1. **Confirm the fourth quality check:** Is type/schema validation the intended fourth check, or does the assignment expect a different category (e.g., business-rule validation)?
2. **What are the exact business rules** for `segment_type` (High-Value / Repeat / One-Time / Inactive)?
3. **How should `lifetime_value_actual` be calculated** relative to source `lifetime_value`?
4. **Should Gold aggregations include only Silver-valid rows**, and what is the exact filter on `quality_check_result`?
5. **Is `gold/03_daily_weekly_trends.sql` in scope** for core completion or stretch only?
6. **Should uniqueness on `customer_id` apply only to the customers table**, not orders?
7. **Should products have Silver quality checks** (e.g., NULL `product_name`, duplicate `product_id`) even though no intentional issues are specified?
8. **Are cancelled/pending orders included** in revenue and order-count metrics?
9. **What is the expected format** of the quality metrics report (table, JSON, notebook output, Delta table)?
10. **Should `payment_date` or order amount consistency** be validated under business logic if that optional module is implemented?
