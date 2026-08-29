# AI Prompt 10 - Silver Layer Implementation

> **File:** `10` of `12` in `ai-prompts/`  
> **Global prompts covered:** 9-11 (verbatim summaries for 9-11 appear in `09-complete-prompt-history.md`)  
> **Evidence:** git commits `212ffc6`, `720ffee`, `ca35a6d`; `src/silver/` implementation

## Purpose / Context

With Bronze complete and validated on Databricks (`workspace.bronze.*`), the next phase was the Silver layer: apply data quality checks, **flag** invalid records, and produce a quality metrics report without deleting rows.

This document records the AI-assisted development journey for Silver, reconstructed from:

- `09-complete-prompt-history.md` (Prompts 9-11)
- Git commits `212ffc6`, `720ffee`, `ca35a6d` on `feature/silver-layer`
- Implemented code under `src/silver/`
- Design artifacts: `requirements-analysis.md`, `data-quality-strategy.md`, `02-refine-requirements.md`

**Repository:** `databricks-medallion-pipeline-st-9124`  
**Branch:** `feature/silver-layer`

---

## Prompt 9 - Silver analysis only (no code)

> **Source:** Verbatim summary preserved in `09-complete-prompt-history.md` (Prompt 9).

### User request (summary)

On branch `feature/silver-layer`, analyze and plan Silver **without writing code**:

- Inspect repo, assignment, design docs, Bronze, config, README, ai-prompts
- Bronze complete on Databricks (`workspace.bronze.*`, 500/10K/100K rows)
- Deliver: Silver transformations per entity, intentional defects, architecture (folder structure, modules, flagging, write strategy, UC targets), config changes, step-by-step plan
- **Do not** modify files, write code, commit, or push

### Outcome

Detailed analysis and implementation plan provided covering:

- Validate-and-flag (no delete/dedup/fix)
- Four core checks + `quality_metrics` reporting
- Processing order: products -> customers -> orders
- Proposed `src/silver/` structure
- Config additions: `SILVER_SCHEMA`, `SILVER_WRITE_MODE`, `EXPECTED_MIN_FAILURE_ROWS`

**See:** `09-complete-prompt-history.md` (Prompt 9)

---

## Prompt 10 - Implement Silver layer

> **Source:** Verbatim summary preserved in `09-complete-prompt-history.md` (Prompt 10).

### User request (summary)

Implement Silver on `feature/silver-layer`:

- Read `workspace.bronze.*`, write `workspace.silver.*` + `quality_metrics`
- 100% row retention; flag with `quality_check_result`, `quality_failure_reasons`, `_silver_processed_at`
- Checks: Completeness, Uniqueness, Type/domain, Referential integrity (orders vs Silver parents)
- Detailed failure codes: `COMPLETENESS_EMAIL`, `COMPLETENESS_CUSTOMER_ID`, etc.
- Add `SILVER_SCHEMA`, `SILVER_WRITE_MODE` to config
- Modular: utilities, check modules, orchestrator, `validate_silver.py`
- **Do not** implement business logic yet
- **Do not** modify README or ai-prompts
- Stop for review

### AI response summary

Created the full `src/silver/` package and updated `src/config.py` and `database/schema.sql`. Bronze code was left unchanged.

**Git commit:** `212ffc6` - Implement Silver data quality layer

### Files created

| File | Purpose |
|------|---------|
| `src/silver/silver_utils.py` | Shared utilities, quality column init, failure appending, metrics write |
| `src/silver/quality_codes.py` | Failure reason code constants |
| `src/silver/01_quality_completeness.py` | NULL checks on critical fields |
| `src/silver/02_quality_uniqueness.py` | Duplicate key detection |
| `src/silver/03_quality_type_validation.py` | Domain / range validation |
| `src/silver/04_quality_referential_integrity.py` | Orphan FK checks on orders |
| `src/silver/05_quality_business_logic.py` | Stub placeholder (not wired) |
| `src/silver/create_silver_tables.py` | Orchestrator |
| `src/silver/validate_silver.py` | Post-processing validation |

---

## Data quality strategy (working decision)

From `02-refine-requirements.md` and `requirements-analysis.md`:

| # | Core check | Rationale |
|---|------------|-----------|
| 1 | **Completeness** | Assignment explicitly requires NULL checks on critical fields |
| 2 | **Uniqueness** | Assignment requires duplicate key detection |
| 3 | **Type/schema validation** | Chosen as fourth core check (repo includes `03_quality_type_validation.py`; assignment names only three checks explicitly) |
| 4 | **Referential integrity** | Assignment requires orphan FK detection |

**Cross-cutting output:** `quality_metrics` table with `% passed` per check - not counted as a fifth check.

**Extension (not active):** `05_quality_business_logic.py` - business-rule validation documented as optional/stretch.

---

## Silver processing flow

```
Bronze Delta (products, customers, orders)
  -> init quality columns (PASS / null reasons)
  -> completeness checks
  -> uniqueness checks
  -> type validation checks
  -> referential integrity (orders only, vs Silver parents)
  -> finalize (_silver_processed_at)
  -> write Silver Delta (same row count as Bronze)
  -> write quality_metrics
  -> validate_silver()
```

**Processing order:** products -> customers -> orders (parents before child for RI).

---

## Check modules (actual implementation)

### 1. Completeness (`01_quality_completeness.py`)

| Entity | Field(s) | Failure code |
|--------|----------|--------------|
| customers | `email` | `COMPLETENESS_EMAIL` |
| orders | `customer_id`, `product_id` | `COMPLETENESS_CUSTOMER_ID`, `COMPLETENESS_PRODUCT_ID` |
| products | `product_id`, `product_name` | `COMPLETENESS_PRODUCT_ID`, `COMPLETENESS_PRODUCT_NAME` |

### 2. Uniqueness (`02_quality_uniqueness.py`)

| Entity | Key | Failure code |
|--------|-----|--------------|
| customers | `customer_id` | `UNIQUENESS_CUSTOMER_ID` |
| orders | `order_id` | `UNIQUENESS_ORDER_ID` |
| products | `product_id` | `UNIQUENESS_PRODUCT_ID` |

Uses window `count()` over partition key; flags all rows in duplicate groups.

### 3. Type validation (`03_quality_type_validation.py`)

| Entity | Rule | Failure code |
|--------|------|--------------|
| customers | Invalid `customer_segment` enum | `TYPE_VALIDATION` |
| orders | Invalid `order_status`; `quantity <= 0` | `TYPE_VALIDATION` |
| products | Negative `stock_quantity` or `reorder_level` | `TYPE_VALIDATION` |

### 4. Referential integrity (`04_quality_referential_integrity.py`)

| Entity | Rule | Failure code |
|--------|------|--------------|
| orders | `customer_id` not in Silver customers | `RI_CUSTOMER` |
| orders | `product_id` not in Silver products | `RI_PRODUCT` |

### 5. Business logic (`05_quality_business_logic.py`) - stub

```python
def apply_business_logic_checks(entity, df):
    return df, []
```

**Not loaded** by `create_silver_tables.py`. Exists in repo structure as an extension placeholder only.

---

## Flagging model (retain invalid rows)

From `silver_utils.py`:

- Every row starts as `quality_check_result = 'PASS'`
- Each failed check appends a pipe-delimited code to `quality_failure_reasons` and sets `quality_check_result = 'FAIL'`
- Multiple failures on one row are supported (concatenated codes)
- Orchestrator raises if Silver row count != Bronze row count

**Design principle:** Silver never silently deletes bad data.

---

## Failure codes reference

Defined in `src/silver/quality_codes.py`:

| Code | Check |
|------|-------|
| `COMPLETENESS_EMAIL` | customers |
| `COMPLETENESS_CUSTOMER_ID` | orders |
| `COMPLETENESS_PRODUCT_ID` | orders, products |
| `COMPLETENESS_PRODUCT_NAME` | products |
| `UNIQUENESS_CUSTOMER_ID` | customers |
| `UNIQUENESS_ORDER_ID` | orders |
| `UNIQUENESS_PRODUCT_ID` | products |
| `TYPE_VALIDATION` | all entities |
| `RI_CUSTOMER` | orders |
| `RI_PRODUCT` | orders |

---

## Quality metrics reporting

`write_quality_metrics()` writes to `workspace.silver.quality_metrics`:

| Column | Description |
|--------|-------------|
| `entity` | customers / orders / products |
| `check_name` | e.g. `completeness_email` |
| `total_rows`, `passed_rows`, `failed_rows` | Counts |
| `pass_pct` | Percentage passed |
| `run_timestamp` | Processing time |

---

## Silver validation (`validate_silver.py`)

Post-processing checks:

| Check | Purpose |
|-------|---------|
| Row retention | Bronze count == Silver count per entity |
| Quality columns | `quality_check_result`, `quality_failure_reasons`, `_silver_processed_at` populated |
| Intentional defects | Minimum failure rows per code (from `EXPECTED_MIN_FAILURE_ROWS` in config) |
| `quality_metrics` | Table exists with rows for all entities |

**Note:** Exact Databricks execution output for Silver validation is not captured in a dedicated ai-prompts execution doc (unlike Bronze in `07`). User-reported status: Silver implemented and validated on Databricks.

---

## Prompt 11 - Fix Silver uniqueness window function

> **Source:** Verbatim summary preserved in `09-complete-prompt-history.md` (Prompt 11).

### User request (summary)

Fix Databricks error `WINDOW_FUNCTION_NOT_ALLOWED_IN_CLAUSE`:

- Materialize `_duplicate_count` column before filter
- Drop `_duplicate_count` before writing Silver table
- Minimal fix only

### Outcome

- **File changed:** `src/silver/02_quality_uniqueness.py` only
- **Git commit:** `720ffee` - Fix Silver uniqueness window check
- Grep confirmed no other window-in-filter usage in Silver

**See:** `09-complete-prompt-history.md` (Prompt 11)

---

## Key design decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Fourth core check | Type validation | Repo structure + four-check acceptance criteria |
| RI parent tables | Silver customers/products (not Bronze) | Consistent flagged parent keys |
| Business logic | Deferred stub | User explicitly said do not implement yet |
| Write mode | `overwrite` | Full pipeline refresh per run |
| UC target | `workspace.silver` | Matches Bronze UC naming |

---

## What I accepted

- Modular check files matching assignment repo structure
- Pipe-delimited `quality_failure_reasons` for multiple failures
- `quality_metrics` as cross-cutting reporting output
- Validation script that verifies intentional defects are flagged
- Window-function fix pattern for Databricks compatibility

## What I rejected

- Deleting or filtering bad rows in Silver
- Implementing business logic in the first Silver release
- Blanket `quality_check_result == 'PASS'` filter for downstream (Gold uses granular eligibility instead)

## Validation

- Silver code structure reviewed against assignment layout
- `validate_silver.py` checks row retention and minimum defect counts
- Uniqueness fix verified for Databricks `WINDOW_FUNCTION_NOT_ALLOWED_IN_CLAUSE`

---

## Related documentation

| File | Purpose |
|------|---------|
| `09-complete-prompt-history.md` | Master index (Prompts 9-11 summarized) |
| `02-refine-requirements.md` | Four-check working decision |
| `data-quality-strategy.md` | DQ rules and thresholds |
| `design-notes.md` | Silver architecture design |
| `src/silver/` | Implementation |
