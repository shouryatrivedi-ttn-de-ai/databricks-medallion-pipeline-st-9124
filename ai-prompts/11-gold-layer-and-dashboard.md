# AI Prompt 11 - Gold Layer and Dashboard

> **File:** `11` of `12` in `ai-prompts/`  
> **Global prompts covered:** 12-18 (reconstructed summaries; see `09-complete-prompt-history.md`)  
> **Evidence:** git commits on `feature/gold-layer` and `master`; `src/gold/`, `src/dashboard/`

## Purpose / Context

With Silver complete and validated, the next phases were:

1. **Gold layer** - business aggregations from eligible Silver data
2. **Dashboard** - Databricks SQL visualizations on Gold tables

This document records the AI-assisted development journey for Gold and Dashboard work, **reconstructed** from:

- Git commits on `feature/gold-layer` (`58ffdee`, `68b8bc9`, `27dcb37`, `ae8922d`, `f3d8519`)
- Merge commit `9fceb4f` (PR #2 into `master`)
- Implemented code under `src/gold/` and `src/dashboard/`
- Conversation history for Gold validation fixes and dashboard alignment (not all captured in earlier ai-prompts)

**Repository:** `databricks-medallion-pipeline-st-9124`  
**Branches:** `feature/gold-layer` (merged to `master`)

---

## Prompt 12 - Gold layer implementation (reconstructed)

### User request (summary, reconstructed)

Implement Gold aggregations on `feature/gold-layer`:

- Read Silver tables from `workspace.silver.*`
- Create three Gold tables: `sales_by_product`, `revenue_by_customer`, `customer_segmentation`
- Use SQL aggregation files + Python orchestrator
- Apply eligibility rules before aggregating (not blanket PASS-only filtering)
- Add Gold validation
- Do not modify Bronze or Silver

### AI response summary

Created `src/gold/` package with SQL aggregations, eligibility logic, orchestrator, and validation.

**Git commit:** `58ffdee` - feat: implement gold layer aggregations

### Files created

| File | Purpose |
|------|---------|
| `src/gold/01_sales_by_product.sql` | Product-level sales metrics |
| `src/gold/02_revenue_by_customer.sql` | Customer-level revenue metrics |
| `src/gold/04_customer_segmentation.sql` | Behavioral segmentation summary |
| `src/gold/eligibility.py` | Eligible orders/products/customers filters |
| `src/gold/gold_utils.py` | Schema setup, SQL render, Silver read |
| `src/gold/create_gold_tables.py` | Orchestrator |
| `src/gold/validate_gold.py` | Post-processing validation |

**Not implemented:** `03_daily_weekly_trends.sql` (optional stretch per design docs).

### Config additions (`src/config.py`)

| Setting | Default |
|---------|---------|
| `GOLD_SCHEMA` | `workspace.gold` |
| `GOLD_WRITE_MODE` | `overwrite` |
| `GOLD_COMPLETED_ORDER_STATUS` | `Completed` |
| `SEGMENTATION_HIGH_VALUE_THRESHOLD` | `1000` |
| `SEGMENT_TYPES` | High-Value, Repeat, One-Time, Inactive |

---

## Gold eligibility logic

From `src/gold/eligibility.py` - filters use `quality_failure_reasons` string matching (NULL reasons = eligible):

| Entity | Rules |
|--------|-------|
| **Orders** | `order_status = Completed` AND no critical codes: `COMPLETENESS_CUSTOMER_ID`, `COMPLETENESS_PRODUCT_ID`, `UNIQUENESS_ORDER_ID`, `RI_CUSTOMER`, `RI_PRODUCT`, `TYPE_VALIDATION` |
| **Products** | No critical codes: `UNIQUENESS_PRODUCT_ID`, `COMPLETENESS_PRODUCT_ID`, `COMPLETENESS_PRODUCT_NAME`, `TYPE_VALIDATION` |
| **Customers** | Only `UNIQUENESS_CUSTOMER_ID` excludes; `COMPLETENESS_EMAIL` does **not** exclude |

Temp views registered for Gold SQL: `eligible_orders`, `eligible_products`, `eligible_customers`.

**Design decision:** Gold uses aggregation-specific eligibility, not a blanket `quality_check_result == 'PASS'` filter.

---

## Gold aggregations

### `workspace.gold.sales_by_product`

- **Source:** `eligible_orders` INNER JOIN `eligible_products`
- **Columns:** `product_id`, `product_name`, `category`, `total_orders`, `total_revenue`, `avg_order_value`
- **Business value:** Product and category performance

### `workspace.gold.revenue_by_customer`

- **Source:** `eligible_orders` INNER JOIN `eligible_customers`
- **Columns:** `customer_id`, `customer_name`, `customer_segment`, `total_orders`, `total_revenue`, `avg_order_value`, `lifetime_value_actual`
- **`lifetime_value_actual`:** sum of eligible completed order revenue (computed, not source `lifetime_value`)
- **Business value:** Customer ranking and CRM analytics

### `workspace.gold.customer_segmentation`

- **Source:** all `eligible_customers` LEFT JOIN their eligible order metrics
- **Segmentation rules** (threshold default 1000):

| Condition | Segment |
|-----------|---------|
| `total_revenue >= threshold` | High-Value |
| `total_orders >= 2` | Repeat |
| `total_orders = 1` | One-Time |
| else | Inactive |

- **Output:** `segment_type`, `customer_count`, `avg_revenue`, `total_revenue`

---

## Gold validation fixes

### Initial validation failures (reconstructed from development session)

After first Gold run on Databricks, `validate_gold.py` reported failures including:

| Check | Issue |
|-------|-------|
| `customer_segmentation.valid_labels` | `expected` and `actual` strings mismatched on success |
| `revenue_by_customer.eligible_revenue_total` | Baseline used all eligible orders, not customer-attributed population |
| `customer_segmentation.eligible_revenue_total` | Same baseline mismatch |
| `revenue_by_customer.eligible_order_count` | Same baseline mismatch |

**Root cause:** Gold SQL correctly uses `INNER JOIN eligible_customers` for customer tables, but validation compared against all eligible orders only.

---

## Prompt 13 - Fix Gold validation baselines (reconstructed)

### User request (summary, reconstructed)

Update `validate_gold.py` only:

- Fix `valid_labels` pass/fail logic
- Use `eligible_orders INNER JOIN eligible_customers` baseline for customer-level checks
- Keep `sales_by_product` checks against full eligible order/product population
- Add cross-table revenue consistency check

**Git commit:** `68b8bc9` - Fix Gold validation baselines

### Validation checks (post-fix)

| Category | Examples |
|----------|----------|
| Table existence | All three Gold tables |
| Row counts | Minimum thresholds |
| Segmentation | Valid labels, customer count, inactive segment |
| Non-negative metrics | No negative revenue/counts |
| Source alignment | Revenue/order totals vs correct eligible populations |
| Cross-table | `revenue_by_customer` total revenue == `customer_segmentation` total revenue |

**Note:** Exact validation output text from Databricks is not stored in ai-prompts; user-reported status is all checks passed after fix.

---

## Git branching and merge workflow

| Step | Branch / action | Evidence |
|------|-----------------|----------|
| Bronze work | `feature/bronze-layer` | Merged via PR #1 (`5e250c2`) |
| Silver work | `feature/silver-layer` | Commits `212ffc6`, `720ffee`, `ca35a6d` |
| Gold work | `feature/gold-layer` | Commits `58ffdee`, `68b8bc9`, `27dcb37`, docs commits |
| Gold merge | PR #2 into `master` | `9fceb4f` |
| Post-merge docs | `master` | `f3d8519`, `ae8922d` dashboard alignment (queries first, then guide) |

**Pattern used:** feature branch per layer, push to remote, merge via pull request. Databricks Git folder pull required after push to sync workspace code.

---

## Prompts 14-18 - Dashboard (reconstructed)

### Prompt 14 - Gold execution on Databricks

User-reported: Gold orchestrator and validation passed on Databricks after Prompt 13 fix. No dedicated execution log file exists in `ai-prompts/` (unlike Bronze in `07`).

### Prompt 15 - Initial dashboard SQL (assignment-style)

**Git commit:** `27dcb37` - Add dashboard queries and documentation

First version of `src/dashboard/dashboard_queries.sql` and `DASHBOARD_GUIDE.md` targeted assignment-style visualizations:

- Top 10 products by revenue (bar)
- Customer revenue distribution (histogram)
- Customer segmentation (pie/donut)

### Deployed dashboard (actual Databricks UI)

The live dashboard built in Databricks uses **four** visualizations (user-confirmed):

| Tile | Chart | Gold source |
|------|-------|-------------|
| Customer Distribution by Segment | Pie / Donut | `customer_segmentation` |
| Total Revenue by Customer Segment | Bar | `customer_segmentation` |
| Top 10 Customers by Revenue | Bar | `revenue_by_customer` |
| Total Revenue by Product Category | Bar | `sales_by_product` |

This differs from the initial assignment-style three-tile layout (histogram, top products).

### Prompts 16-18 - Dashboard review and alignment (post-deploy)

| Global prompt | Topic | Git commit |
|---------------|-------|------------|
| 16 | Dashboard review (filters required, SQL/guide mismatch) | (analysis only; no commit) |
| 17 | Align `dashboard_queries.sql` | `f3d8519` |
| 18 | Align `DASHBOARD_GUIDE.md` | `ae8922d` |

**Final `dashboard_queries.sql` structure:**

| Query | Visualization |
|-------|---------------|
| QUERY 1 | Customer Distribution by Segment |
| QUERY 2 | Total Revenue by Customer Segment |
| QUERY 3 | Top 10 Customers by Revenue (optional `customer_segment` filter) |
| QUERY 4 | Total Revenue by Product Category (optional `product_category` filter) |
| FILTER SUPPORT | Filter value lists with `All` default |

### Dashboard review findings (reconstructed)

A strict review identified:

- README and SQL file were out of sync with deployed dashboard
- Old guide referenced histogram and three-tile layout
- Filters should be documented as required (assignment says "add filters")
- Dual-query filter pattern (QUERY 1/1b) was simplified to single parameterized queries

All fixes were documentation-only; no pipeline code changed.

---

## Databricks execution pattern (Gold)

```python
import os, sys
os.environ["BRONZE_SCHEMA"] = "workspace.bronze"
os.environ["SILVER_SCHEMA"] = "workspace.silver"
os.environ["GOLD_SCHEMA"] = "workspace.gold"
sys.path.insert(0, repo_root)
from src.gold.create_gold_tables import main
exit(main())
```

Dashboard queries run separately in Databricks SQL against `workspace.gold.*`.

**Gap:** No dedicated `ai-prompts/` execution doc for Silver/Gold runs (Bronze has `07`). Execution evidence is in user-reported status and git history.

---

## What I accepted

- SQL aggregations with Python orchestrator (matching Bronze/Silver pattern)
- Granular Gold eligibility via failure codes
- Customer-attributed validation baselines
- Four-tile deployed dashboard documented honestly (not forcing assignment histogram layout)
- Parameterized filters with `All` default for safe dashboard behavior

## What I rejected

- Modifying Gold SQL to match incorrect validation baselines
- Keeping dual QUERY 1/1b pattern after review showed confusion risk
- Claiming business logic validation is active in Silver (it is a stub)

## Related documentation

| File | Purpose |
|------|---------|
| `src/dashboard/dashboard_queries.sql` | QUERY 1-4 + filter support |
| `src/dashboard/DASHBOARD_GUIDE.md` | Databricks UI setup |
| `README.md` | Project overview and dashboard summary |
| `09-complete-prompt-history.md` | Master index |
| `12-final-project-polish.md` | README and portfolio polish phase |
