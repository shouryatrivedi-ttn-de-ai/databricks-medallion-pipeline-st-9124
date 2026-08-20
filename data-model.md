# Data Model

> **Status:** Technical design for review (pre-implementation).  
> **Related:** `design-notes.md`, `requirements-analysis.md`, `docs/assignment.md`

## Overview

Three CSV sources model an e-commerce domain: **customers** and **products** (dimensions) and **orders** (fact). Data flows through Bronze (raw), Silver (quality-flagged), and Gold (aggregated) layers on Databricks Delta tables.

```
customers (1) ──< orders >── (1) products
     │              │
     │              ├── customer_id → customers.customer_id
     │              └── product_id   → products.product_id
     └── customer_id (PK)
```

---

## Source Entities (CSV)

### customers

**File:** `customers.csv` | **Volume:** ~10,000 rows

| Column | Data Type | Nullable | Key | Silver completeness | Notes |
|--------|-----------|----------|-----|---------------------|-------|
| `customer_id` | INT | No* | PK | — | 10 intentional duplicate keys |
| `customer_name` | STRING | Yes | | — | |
| `email` | STRING | Yes | | **Yes** | 50 intentional NULLs |
| `country` | STRING | Yes | | — | |
| `signup_date` | DATE | Yes | | Type check | |
| `customer_segment` | STRING | Yes | | Type check | `Premium`, `Standard`, `Basic` |
| `lifetime_value` | DECIMAL(18,2) | Yes | | Type check | Source attribute; not used as Gold `lifetime_value_actual` *(assumption WD-08)* |

### orders

**File:** `orders.csv` | **Volume:** ~100,000 rows

| Column | Data Type | Nullable | Key | Silver checks | Notes |
|--------|-----------|----------|-----|---------------|-------|
| `order_id` | INT | No* | PK | Uniqueness | 20 intentional duplicate keys |
| `customer_id` | INT | Yes | FK → customers | Completeness, RI | 100 NULLs; 50 orphans |
| `order_date` | DATE | Yes | | Type check | |
| `product_id` | INT | Yes | FK → products | Completeness, RI | 200 NULLs; 30 orphans |
| `quantity` | INT | Yes | | Type check | |
| `unit_price` | DECIMAL(18,2) | Yes | | Type check | |
| `total_amount` | DECIMAL(18,2) | Yes | | Type check | Primary Gold revenue field |
| `order_status` | STRING | Yes | | Type check | `Pending`, `Completed`, `Cancelled` |
| `payment_date` | DATE | Yes (schema) | | Type check | Nullable by assignment |

**Assumption (WD-11):** Gold revenue uses `order_status = 'Completed'` only. Pending and Cancelled excluded from aggregations.

### products

**File:** `products.csv` | **Volume:** ~500 rows

| Column | Data Type | Nullable | Key | Silver checks | Notes |
|--------|-----------|----------|-----|---------------|-------|
| `product_id` | INT | No | PK | Uniqueness | No intentional defects |
| `product_name` | STRING | Yes | | Completeness | |
| `category` | STRING | Yes | | — | Used in Gold sales-by-product |
| `price` | DECIMAL(18,2) | Yes | | Type check | Catalog price |
| `cost` | DECIMAL(18,2) | Yes | | Type check | Not in core Gold output |
| `stock_quantity` | INT | Yes | | Type check | |
| `reorder_level` | INT | Yes | | Type check | |

**Assumption:** Products receive all four Silver checks for pipeline symmetry despite no intentional defects in the assignment.

---

## Relationships

| From | To | Cardinality | Join | Validated in Silver |
|------|-----|-------------|------|---------------------|
| orders | customers | N:1 | `orders.customer_id = customers.customer_id` | RI (orders side) |
| orders | products | N:1 | `orders.product_id = products.product_id` | RI (orders side) |

**Referential integrity rule:** Non-NULL FK on orders must exist in the corresponding Silver parent table. Orphans are flagged, not removed.

---

## Intentional Quality Issues (assignment)

| Entity | Issue | Count | Silver check |
|--------|-------|-------|--------------|
| customers | NULL `email` | 50 | Completeness |
| customers | Duplicate `customer_id` | 10 keys | Uniqueness |
| orders | NULL `customer_id` | 100 | Completeness |
| orders | NULL `product_id` | 200 | Completeness |
| orders | Orphan `customer_id` | 50 | Referential integrity |
| orders | Orphan `product_id` | 30 | Referential integrity |
| orders | Duplicate `order_id` | 20 keys | Uniqueness |
| products | — | 0 | — |

Assignment cites ~700 problematic rows total; exact total depends on how duplicate-key rows are counted. Generator validates counts post-generation.

---

## Medallion Layer Schemas

### Bronze layer (raw + ingest metadata)

Bronze mirrors CSV columns plus metadata. Data is unchanged from source.

**Tables:** `bronze.customers`, `bronze.orders`, `bronze.products`, `bronze.ingestion_log`

| Column | Type | Applies to |
|--------|------|------------|
| *(all CSV columns)* | Per source schema | Entity tables |
| `_ingest_timestamp` | TIMESTAMP | Entity tables |
| `_source_file` | STRING | Entity tables |

**ingestion_log:**

| Column | Type | Description |
|--------|------|-------------|
| `entity` | STRING | customers / orders / products |
| `row_count` | BIGINT | Rows ingested |
| `ingest_timestamp` | TIMESTAMP | When ingest completed |
| `source_path` | STRING | CSV path |

---

### Silver layer (typed + quality-flagged)

Silver retains **every Bronze row**. Adds quality metadata and enforces typed columns.

**Tables:** `silver.customers`, `silver.orders`, `silver.products`, `silver.quality_metrics`

#### Entity tables — quality columns (all Silver entities)

| Column | Type | Description |
|--------|------|-------------|
| `quality_check_result` | STRING | `PASS` or `FAIL` |
| `quality_failure_reasons` | STRING | Pipe-separated codes, e.g. `COMPLETENESS\|UNIQUENESS` |
| `_silver_processed_at` | TIMESTAMP | When Silver processing ran |

**Overall vs aggregation eligibility:** `quality_check_result` reflects whether **any** check failed (drives `quality_metrics`). Gold does not treat every `FAIL` as a global exclusion—see critical vs non-critical table under Gold layer.

| Code | Check |
|------|-------|
| `COMPLETENESS` | NULL in critical field |
| `UNIQUENESS` | Duplicate PK |
| `TYPE_VALIDATION` | Invalid type, date, or enum |
| `RI_CUSTOMER` | Orphan `customer_id` on orders |
| `RI_PRODUCT` | Orphan `product_id` on orders |
| `BUSINESS_LOGIC` | Optional stretch only |

#### Four core checks — scope by table

| Check | customers | orders | products |
|-------|-----------|--------|----------|
| Completeness | `email` | `customer_id`, `product_id` | `product_id`, `product_name` |
| Uniqueness | `customer_id` | `order_id` | `product_id` |
| Type/schema | IDs, dates, segment enum, decimals | IDs, dates, status enum, decimals | IDs, decimals |
| Referential integrity | — | FK → customers, products | — |

#### quality_metrics (cross-cutting report)

| Column | Type | Description |
|--------|------|-------------|
| `run_timestamp` | TIMESTAMP | Report run time |
| `entity` | STRING | Table checked |
| `check_name` | STRING | completeness / uniqueness / type_validation / ri_customer / ri_product |
| `total_rows` | BIGINT | Rows evaluated |
| `passed_rows` | BIGINT | Rows passing this check |
| `failed_rows` | BIGINT | Rows failing this check |
| `pass_pct` | DECIMAL(5,2) | Percentage passed |

---

### Gold layer (business aggregations)

Gold tables apply **aggregation-specific eligibility** *(assumption WD-07)*—critical Silver failures block participation in a given aggregation; non-critical failures do not globally exclude records.

**Order fact filter *(WD-11)*:** `order_status = 'Completed'` for revenue/order metrics.

**Tables:** `gold.sales_by_product`, `gold.revenue_by_customer`, `gold.customer_segmentation`

#### Critical vs non-critical failures (Gold consumption)

Silver retains `quality_check_result = 'FAIL'` when any check fails. Gold uses **per-aggregation criticality** instead of excluding all `FAIL` rows:

| Entity | Critical (blocks aggregation) | Non-critical (flagged; may still be usable) |
|--------|------------------------------|---------------------------------------------|
| **orders** | `COMPLETENESS`, `UNIQUENESS`, `RI_CUSTOMER`, `RI_PRODUCT`, `TYPE_VALIDATION` on key fields (`order_id`, FKs, `total_amount`, `order_status`) | `TYPE_VALIDATION` on unused fields (e.g. `payment_date`) |
| **customers** | `UNIQUENESS`, `TYPE_VALIDATION` on `customer_id` | `COMPLETENESS` (`email`), `TYPE_VALIDATION` on unused fields (e.g. `lifetime_value`, `signup_date`) |
| **products** | `UNIQUENESS`, `COMPLETENESS` on `product_id`/`product_name`, `TYPE_VALIDATION` on `product_id` | `TYPE_VALIDATION` on unused fields (e.g. `stock_quantity`) |

**Helper concepts:**

| View | Definition |
|------|------------|
| `aggregation_eligible_orders` | Completed orders with no critical order failure |
| `segmentation_eligible_customers` | Customers with no `UNIQUENESS` failure (NULL email allowed) |
| `revenue_eligible_customers` | Segmentation-eligible customers with ≥ 1 aggregation-eligible order |
| `product_eligible_products` | Products with no critical product failure |

#### gold.sales_by_product

| Column | Type | Description |
|--------|------|-------------|
| `product_id` | INT | PK (grain) |
| `product_name` | STRING | From product-eligible products |
| `category` | STRING | From products |
| `total_orders` | BIGINT | Distinct aggregation-eligible orders |
| `total_revenue` | DECIMAL(18,2) | Sum of `total_amount` |
| `avg_order_value` | DECIMAL(18,2) | `total_revenue / total_orders` |

**Join pattern:** `aggregation_eligible_orders` INNER JOIN `product_eligible_products`.

#### gold.revenue_by_customer

| Column | Type | Description |
|--------|------|-------------|
| `customer_id` | INT | PK (grain) |
| `customer_name` | STRING | From customers |
| `customer_segment` | STRING | Source tier: Premium/Standard/Basic |
| `total_orders` | BIGINT | Aggregation-eligible orders per customer |
| `total_revenue` | DECIMAL(18,2) | Sum of `total_amount` |
| `avg_order_value` | DECIMAL(18,2) | `total_revenue / total_orders` |
| `lifetime_value_actual` | DECIMAL(18,2) | **Assumption (WD-08):** sum of aggregation-eligible completed order revenue |

**Join pattern:** INNER JOIN — **revenue-eligible customers** only (≥ 1 eligible order). Customers with zero eligible orders excluded here; they appear in segmentation as **Inactive**.

**Example:** Customer with NULL `email` but eligible orders **can appear** in this table.

#### gold.customer_segmentation

**Assignment defines labels only.** Segment rules are design assumptions *(WD-09)*. Thresholds unchanged.

| Column | Type | Description |
|--------|------|-------------|
| `segment_type` | STRING | `High-Value`, `Repeat`, `One-Time`, `Inactive` |
| `customer_count` | BIGINT | Customers in segment |
| `avg_revenue` | DECIMAL(18,2) | Mean of per-customer `total_revenue` in segment |
| `total_revenue` | DECIMAL(18,2) | Sum of per-customer `total_revenue` in segment |

**Join pattern (customers-first LEFT JOIN):**

```
segmentation_eligible_customers
  LEFT JOIN (
    aggregation_eligible_orders GROUP BY customer_id
  ) customer_order_metrics USING (customer_id)
  → COALESCE(total_orders, 0), COALESCE(total_revenue, 0)
```

This preserves customers with **zero aggregation-eligible orders** as `total_orders = 0` → **Inactive**.

**Assumed segment assignment (mutually exclusive, priority order):**

| segment_type | Condition *(assumption)* |
|--------------|--------------------------|
| High-Value | `total_revenue >= 1000` |
| Repeat | `total_orders >= 2` (and not High-Value) |
| One-Time | `total_orders = 1` |
| Inactive | `total_orders = 0` |

Customers with critical `UNIQUENESS` failure are excluded from segmentation (ambiguous identity). All other segmentation-eligible customers appear in exactly one segment.

---

## Pipeline Data Flow

```
data/*.csv
    │  (generate_sample_data.py)
    ▼
DBFS/S3 path
    │  (bronze ingest — no transforms)
    ▼
bronze.{customers,orders,products}
    │  (silver — 4 checks, flag all rows)
    ▼
silver.{customers,orders,products}  +  silver.quality_metrics
    │  (gold — aggregation-specific eligibility + Completed filter)
    ▼
gold.{sales_by_product,revenue_by_customer,customer_segmentation}
    │  (Databricks SQL Dashboard)
    ▼
3+ dashboard visualizations
```

---

## Physical Types (Databricks / Delta)

| Logical | Spark / Delta type |
|---------|-------------------|
| INT | `INT` |
| STRING | `STRING` |
| DATE | `DATE` |
| TIMESTAMP | `TIMESTAMP` |
| DECIMAL | `DECIMAL(18,2)` |

Explicit schemas defined in `database/schema.sql` and used in Bronze read, Silver write, and Gold DDL.

---

## Data Volume Summary

| Layer | Table | Approx. rows |
|-------|-------|--------------|
| Source | customers | 10,000 |
| Source | orders | 100,000 |
| Source | products | 500 |
| Bronze | *(same as source)* | |
| Silver | *(same as Bronze — all rows retained)* | |
| Gold | sales_by_product | ≤ 500 *(products with sales)* |
| Gold | revenue_by_customer | ≤ 10,000 *(customers with ≥ 1 eligible order)* |
| Gold | customer_segmentation | 4 *(segment grain)*; Inactive count > 0 expected |

---

## Design Assumptions vs Assignment Requirements

| Topic | Assignment says | Our design *(assumption)* |
|-------|-----------------|---------------------------|
| Fourth Silver check | Four required; three named | Type/schema validation |
| Bad rows | Flag, don't delete | All rows in Silver; Gold uses aggregation-specific criticality |
| Gold eligibility | Not specified | Critical failures block specific aggregations; non-critical (e.g. NULL email) may still be usable |
| Segmentation — Inactive | Label defined only | Customers-first LEFT JOIN to order metrics; zero eligible orders → Inactive |
| `lifetime_value_actual` | Column named in Gold | Sum of aggregation-eligible completed order revenue |
| Segmentation rules | Four labels only | Revenue/order-count thresholds unchanged ($1000 / 2+ / 1 / 0) |
| Order status in Gold | Not specified | Completed orders only for revenue |
| Products Silver QA | Not specified | Full four checks applied |
| Quality report format | % passed required | Delta table `silver.quality_metrics` |
| daily_weekly_trends | Not in core Gold spec | Optional/stretch |

See `requirements-analysis.md` for the full ambiguity list.
