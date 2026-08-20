# Data Quality Strategy

## Overview

Silver-layer data quality validates three Bronze CSV sources across **completeness**, **uniqueness**, and **referential integrity**, with optional **type** and **business-rule** validations matching the repository template. Invalid records are **flagged, not deleted**. A metrics report quantifies pass rates per check.

> **Spec note:** The assignment repeatedly requires "four quality checks" while the repository lists five Silver modules (`type_validation`, `business_logic`). This strategy treats Completeness, Uniqueness, Referential Integrity, and Quality Reporting as the **four core checks**; Type Validation and Business Logic are **documented extensions** aligned with repo structure.

---

## Quality Checks Overview

| # | Check | Primary Tables | Critical Fields / Keys |
|---|-------|----------------|------------------------|
| 1 | Completeness | customers, orders | `email`; `customer_id`, `product_id` |
| 2 | Uniqueness | customers, orders | `customer_id`; `order_id` |
| 3 | Referential Integrity | orders | `customer_id` → customers; `product_id` → products |
| 4 | Quality Reporting | all Silver | Aggregates outcomes; `quality_check_result` |
| 5* | Type Validation (optional) | all | Parseable types, valid enums |
| 6* | Business Logic (optional) | orders | Amount consistency, status rules |

---

## 1. Completeness Check

### What

Ensure critical fields required for downstream analytics are not NULL.

### Scope

| Table | Field | Required? | Intentional NULL Count |
|-------|-------|-----------|------------------------|
| `customers` | `email` | Yes | 50 |
| `customers` | `customer_id` | Yes (PK) | 0 (not injected) |
| `orders` | `customer_id` | Yes | 100 |
| `orders` | `product_id` | Yes | 200 |
| `products` | `product_id` | Yes (PK) | 0 |

**Not in scope (unless extended):** `payment_date` (explicitly nullable), `customer_name`, descriptive attributes.

### How

```sql
-- Example: orders completeness
SELECT *,
  CASE
    WHEN customer_id IS NULL THEN 'FAIL'
    WHEN product_id IS NULL THEN 'FAIL'
    ELSE 'PASS'
  END AS completeness_result
FROM bronze.orders
```

PySpark implementation uses column-wise `isNull()` checks combined with `when/otherwise`.

### Threshold

| Source | Threshold |
|--------|-----------|
| Submission template | >99% complete per field |
| Intentional data | ~99.5%+ on orders for each FK field; ~99.5% email completeness on customers |

Report actual % passed; threshold is informational unless stakeholder clarifies enforcement.

### Result

- Flag rows with any NULL in scoped critical fields.
- Failure code: `COMPLETENESS`.

---

## 2. Uniqueness Check

### What

Ensure primary key values are unique within their entity table.

### Scope

| Table | Key | Intentional Duplicate Keys |
|-------|-----|------------------------------|
| `customers` | `customer_id` | 10 duplicate key values (≥20 rows affected if pairwise) |
| `orders` | `order_id` | 20 duplicate key values |

**Clarification:** Uniqueness on `customer_id` applies to the **customers** table, not orders (many orders per customer is valid).

### How

```sql
-- Identify duplicate order_id values
SELECT order_id, COUNT(*) AS cnt
FROM bronze.orders
GROUP BY order_id
HAVING COUNT(*) > 1
```

Flag **all rows** participating in a duplicate key group (not just the "second" occurrence)—consistent audit behavior.

### Threshold

| Source | Threshold |
|--------|-----------|
| Submission template | 100% unique on PKs |
| Expected on generated data | ~99.98% unique on order_id; ~99.9% on customer_id |

### Result

- Failure code: `UNIQUENESS`.

---

## 3. Referential Integrity Check

### What

Ensure foreign keys in orders reference existing parent keys.

### Scope

| Child Table | FK Column | Parent Table | Parent Key | Intentional Orphans |
|-------------|-----------|--------------|------------|---------------------|
| `orders` | `customer_id` | `customers` | `customer_id` | 50 (non-NULL FK not in parent) |
| `orders` | `product_id` | `products` | `product_id` | 30 (non-NULL FK not in parent) |

### How

Left anti-join pattern:

```sql
-- Orphan customer_id
SELECT o.*
FROM silver.orders o
LEFT JOIN silver.customers c ON o.customer_id = c.customer_id
WHERE o.customer_id IS NOT NULL AND c.customer_id IS NULL
```

**NULL FK handling:** NULL `customer_id` / `product_id` fails **Completeness**, not RI (RI evaluated only when FK IS NOT NULL).

Use **Silver customers/products** (or Bronze if Silver parents not yet built) as reference—prefer Silver parents after their own checks so duplicate PK parents are visible.

### Threshold

| Source | Threshold |
|--------|-----------|
| Submission template | >99.9% valid FK references |
| Expected | ~99.92% valid customer_id; ~99.77% valid product_id among non-NULL FKs |

### Result

- Failure codes: `RI_CUSTOMER`, `RI_PRODUCT` (distinct for traceability).

---

## 4. Type / Business-Rule Validation (Optional Extensions)

### Type Validation

| Table | Rules |
|-------|-------|
| All | IDs cast to INT; dates cast to DATE; decimals cast to DECIMAL(18,2) |
| `customers` | `customer_segment IN ('Premium','Standard','Basic')` |
| `orders` | `order_status IN ('Pending','Completed','Cancelled')` |
| `products` | `stock_quantity`, `reorder_level` ≥ 0 |

Failure code: `TYPE_VALIDATION`.

### Business Logic Validation

| Rule | Logic | Notes |
|------|-------|-------|
| Order amount consistency | `ABS(total_amount - quantity * unit_price) <= 0.01` | Not an intentional defect; catches generator drift |
| Payment date logic | `order_status = 'Completed' AND payment_date IS NULL` → warn/fail | Optional strictness |
| Quantity positive | `quantity > 0` for completed orders | Optional |

Failure code: `BUSINESS_LOGIC`.

---

## Expected Intentional Data-Quality Issues

### customers.csv

| Issue Type | Count | Detection Check |
|------------|-------|-----------------|
| NULL `email` | 50 | Completeness |
| Duplicate `customer_id` | 10 keys | Uniqueness |

### orders.csv

| Issue Type | Count | Detection Check |
|------------|-------|-----------------|
| NULL `customer_id` | 100 | Completeness |
| NULL `product_id` | 200 | Completeness |
| Invalid `customer_id` (orphan) | 50 | Referential Integrity |
| Invalid `product_id` (orphan) | 30 | Referential Integrity |
| Duplicate `order_id` | 20 keys | Uniqueness |

### products.csv

| Issue Type | Count |
|------------|-------|
| None specified | 0 |

### Total

Assignment states **~700 problematic rows** out of ~110,500 (~0.7%). Exact total depends on how duplicate-key rows are counted (each duplicate row vs unique defect keys). The generator must document final counts and align tests to actuals.

---

## How Bad Records Should Be Flagged

### Row-Level Flagging

Each Silver table row includes:

| Column | Example Value | Description |
|--------|---------------|-------------|
| `quality_check_result` | `PASS` / `FAIL` | Overall row status |
| `quality_failure_reasons` | `COMPLETENESS\|RI_CUSTOMER` | Pipe-delimited failure codes |

### Flagging Rules

1. Default `quality_check_result = 'PASS'`.
2. Any failed check sets `quality_check_result = 'FAIL'`.
3. Accumulate all failure codes in `quality_failure_reasons`.
4. **Never drop** failed rows from Silver tables.
5. Gold layer excludes `FAIL` rows from aggregations (assumption).

### Duplicate Key Handling

All rows sharing a duplicated PK receive `FAIL` + `UNIQUENESS`—avoids arbitrary "keeper" logic in Silver.

---

## How Quality Metrics Should Be Calculated

### Per-Check Metrics

For each check *C* on entity *E*:

```
total_rows       = COUNT(*) FROM silver.<E>
failed_rows      = COUNT(*) WHERE quality_failure_reasons LIKE '%<CODE>%'
                   OR check-specific predicate
passed_rows      = total_rows - failed_rows  (or count PASS for that dimension)
pass_pct         = (passed_rows / total_rows) * 100
```

### Report Schema (`silver.quality_metrics`)

| Column | Type | Description |
|--------|------|-------------|
| `run_id` | STRING | Batch/run identifier |
| `run_timestamp` | TIMESTAMP | When checks executed |
| `entity` | STRING | customers / orders / products |
| `check_name` | STRING | completeness / uniqueness / ri_customer / ri_product / ... |
| `total_rows` | BIGINT | Rows evaluated |
| `passed_rows` | BIGINT | Rows passing this check |
| `failed_rows` | BIGINT | Rows failing this check |
| `pass_pct` | DECIMAL(5,2) | Percentage passed |

### Example Expected Results (Approximate)

| Check | Entity | Expected pass_pct (approx.) |
|-------|--------|----------------------------|
| Completeness (email) | customers | 99.50% |
| Uniqueness (customer_id) | customers | 99.90%+ |
| Completeness (customer_id) | orders | 99.90% |
| Completeness (product_id) | orders | 99.80% |
| Uniqueness (order_id) | orders | 99.98% |
| RI (customer_id) | orders | 99.85%+ among non-NULL |
| RI (product_id) | orders | 99.69%+ among non-NULL |

Exact numbers validated post-generation.

### Presentation

1. **Delta table** `silver.quality_metrics` for programmatic access.
2. **Console/notebook summary** after `create_silver_tables.py`:

   ```
   Check                  Entity     Pass %
   ─────────────────────────────────────────
   Completeness (email)   customers  99.50
   Uniqueness (order_id)  orders     99.98
   ...
   ```

3. Tests assert failed row counts ≥ intentional minimums.

---

## Overlap and Precedence

| Scenario | Failed Checks |
|----------|---------------|
| NULL `customer_id` on order | COMPLETENESS (not RI) |
| Orphan non-NULL `customer_id` | RI_CUSTOMER |
| Duplicate `order_id` | UNIQUENESS (+ possibly bad aggregates if included in Gold) |
| Row fails multiple checks | All applicable codes in `quality_failure_reasons` |

---

## Validation Before Task Complete

Before considering Silver QA done:

1. Run generator and confirm defect injection counts in `DATA_GENERATION_NOTES.md`.
2. Execute Silver pipeline on full dataset.
3. Verify `quality_metrics` pass_pct aligns with expected rates.
4. Run automated tests asserting minimum failed-row counts per issue type.
5. Confirm Gold row counts drop appropriately vs Bronze (only PASS + business-filtered rows contribute).

---

## Open Items (Pending Clarification)

1. Whether type/business modules count toward "four checks" for acceptance.
2. Whether submission template thresholds (>99%, 100%, >99.9%) are gates or reporting guidelines.
3. Whether products require formal Silver checks despite no intentional defects.
4. Whether `quality_check_result` uses `PASS/FAIL` strings or a richer enum.
