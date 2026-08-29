# Complete Project Prompt History

> Master index of all user prompts and requests across the Databricks Medallion pipeline project.  
> Individual stage details also live in `01`–`08` where noted.

**Repository:** `databricks-medallion-pipeline-st-9124`  
**Last updated:** After Silver uniqueness window-function fix

---

## How to use this file

| File | Covers |
|------|--------|
| `01-requirements-analysis.md` | Initial requirements analysis |
| `02-refine-requirements.md` | Silver four-check working decision |
| `03-architecture-design.md` | CSV → Bronze → Silver → Gold design |
| `04-sample-data-generation.md` | Sample data generator + integer CSV fix |
| `05-bronze-layer-implementation.md` | Bronze layer code |
| `06-bronze-layer-review-and-improvements.md` | Bronze read-path review, FAILFAST |
| `07-bronze-databricks-execution-and-troubleshooting.md` | Databricks Bronze execution |
| `08-git-and-databricks-troubleshooting-history.md` | Git/auth/%run troubleshooting |
| **This file (`09`)** | Full chronological prompt history |

---

## Prompt 1 — Greeting / session start

### User request

> hi / HI

### Intent

Session opener before starting implementation work.

### Outcome

Assistant reviewed the assignment spec and repo, then proceeded with sample data generation when the full task was given.

---

## Prompt 2 — Implement sample data generator

### User request (summary)

Implement sample data generation under `src/data_generation/`:

- Python + Faker/pandas, fixed random seed
- Generate `customers.csv`, `orders.csv`, `products.csv`
- Include intentional data-quality issues from the assignment (not clean data)
- Self-validate defect counts after generation
- Modular and readable
- **Do not** implement Bronze, Silver, Gold, or dashboard yet
- Explain files created and how to run/validate

### Key requirements captured

| Item | Value |
|------|-------|
| customers | 10,000 rows |
| orders | 100,000 rows |
| products | 500 rows |
| Seed | 42 |
| Defects | 50 NULL emails, 10 duplicate customer_id keys, 100 NULL customer_id, 200 NULL product_id, 50 orphan customer_id, 30 orphan product_id, 20 duplicate order_id keys |

### Outcome

- Created `src/data_generation/` (config, generators, validation, orchestrator, notes)
- Wrote CSVs to `data/`
- All seven defect-count validations passed
- **See:** `04-sample-data-generation.md`

---

## Prompt 3 — Explain data generator (educational)

### User request

> how do u create a data generator ? whats the core logic? explain in easy terms

### Intent

Conceptual explanation only — no code changes.

### Outcome

Plain-language explanation of:

1. Set rules (counts, columns, seed)
2. Generate parent tables first (products → customers)
3. Generate child tables (orders) with valid FKs
4. Inject intentional bad data
5. Export CSV
6. Validate defect counts

Mental model: `Rules → Clean Data → Inject Defects → Export CSV → Validate`

---

## Prompt 4 — Implement Bronze layer

### User request (summary)

Implement Bronze ingestion under `src/bronze/`:

- Read three generated CSVs → Delta tables
- Keep source unchanged — no clean/dedup/reject/business validation
- Add `_ingest_timestamp`, `_source_file` only
- Explicit schemas (preserve intentional NULLs and invalid values)
- Modular, Databricks PySpark job ready
- Simple validation: row counts + metadata
- **Do not** implement Silver, Gold, or dashboard

### Outcome

- Created Bronze modules, `src/config.py`, `database/schema.sql`
- Initial read path: string read + manual cast (later revised in Prompt 6)
- **See:** `05-bronze-layer-implementation.md`

---

## Prompt 5 — Review and fix Bronze read path

### User request (summary)

Review `read_csv_raw` and `cast_to_schema`:

- Bronze must not silently convert malformed values to NULL via cast
- Simplify to direct explicit schema CSV read where possible
- Preserve intentional NULLs, duplicates, orphan IDs
- Remove unnecessary transformation logic
- Keep metadata, Delta writes, ingestion log, validation unchanged
- **Do not** implement Silver logic

### Outcome

- Removed string read + manual cast
- Added direct schema read with `FAILFAST`
- Identified pandas `2529.0` integer CSV issue (fixed in Prompt 6)
- **See:** `06-bronze-layer-review-and-improvements.md`

---

## Prompt 6 — Fix integer CSV export in generator

### User request (summary)

Before running Bronze, fix generator so integer columns write as integers (not `2529.0`):

- **Only** CSV output formatting for nullable integer columns
- **Do not** change row counts, defect counts, seed, or quality scenarios
- Regenerate CSVs and re-run data-generation validation
- **Do not** modify Bronze, Silver, Gold, or dashboard

### Outcome

- Updated `write_csv()` to use pandas nullable `Int64` before export
- Regenerated CSVs; all defect validations passed again
- **See:** `04-sample-data-generation.md` (follow-up section)

---

## Prompt 7 — Document Bronze journey (prompt history + README)

### User request (summary)

Document complete Bronze implementation journey in `ai-prompts/`:

- Create `07-bronze-databricks-execution-and-troubleshooting.md`
- Create `08-git-and-databricks-troubleshooting-history.md`
- Minimal README update for Bronze status
- **Do not** modify Bronze Python code
- **Do not** overwrite existing ai-prompts
- Capture: Unity Catalog Volume, Databricks Git auth, `%run` failure, sys.path import fix, successful execution (500/10K/100K), validation pass, Git branch `feature/bronze-layer`, push troubleshooting

### Outcome

- Created prompts 07 and 08
- Created minimal `README.md` with Bronze status
- **See:** `07-bronze-databricks-execution-and-troubleshooting.md`, `08-git-and-databricks-troubleshooting-history.md`

---

## Prompt 8 — Adapt Bronze for Unity Catalog Volume

### User request (summary)

Adapt Bronze for local + Databricks Unity Catalog Volume:

1. **`src/config.py`:** Keep local `DEFAULT_DATA_PATH`, env `DATA_PATH`, default `BRONZE_SCHEMA=workspace.bronze`, do not hardcode Volume path
2. **`resolve_csv_path()`:** Local pathlib checks; for `/Volumes/` paths return `{DATA_PATH}/{filename}` without `Path.exists()`
3. Table naming: `workspace.bronze.customers|orders|products|ingestion_log`
4. Check three-level Unity Catalog table name compatibility
5. **Do not** change Bronze ingestion logic, schemas, validation, data generation

### Outcome

- Updated `src/config.py` (`BRONZE_SCHEMA` default → `workspace.bronze`)
- Updated `resolve_csv_path()` Volume branch
- Confirmed existing `f"{BRONZE_SCHEMA}.{entity}"` works for UC three-part names

---

## Prompt 9 — Silver layer analysis only (no code)

### User request (summary)

On branch `feature/silver-layer`, analyze and plan Silver **without writing code**:

- Inspect repo, assignment, design docs, Bronze, config, README, ai-prompts
- Bronze complete on Databricks (`workspace.bronze.*`, 500/10K/100K rows)
- Deliver: Silver transformations per entity, intentional defects, architecture (folder structure, modules, flagging, write strategy, UC targets), config changes, step-by-step plan
- **Do not** modify files, write code, commit, or push
- Stop and wait for approval

### Outcome

Detailed analysis and implementation plan provided covering:

- Validate-and-flag (no delete/dedup/fix)
- Four core checks + quality_metrics
- Processing order: products → customers → orders
- Proposed `src/silver/` structure
- Config additions: `SILVER_SCHEMA`, `SILVER_WRITE_MODE`, `EXPECTED_MIN_FAILURE_ROWS`

---

## Prompt 10 — Implement Silver layer

### User request (summary)

Implement Silver on `feature/silver-layer`:

- Read `workspace.bronze.*`, write `workspace.silver.*` + `quality_metrics`
- 100% row retention; flag with `quality_check_result`, `quality_failure_reasons`, `_silver_processed_at`
- Checks: Completeness, Uniqueness, Type/domain, RI (orders vs Silver parents)
- Detailed failure codes: `COMPLETENESS_EMAIL`, `COMPLETENESS_CUSTOMER_ID`, etc.
- Add `SILVER_SCHEMA`, `SILVER_WRITE_MODE` to config
- Modular: utilities, check modules, orchestrator, `validate_silver.py`
- **Do not** implement business logic yet
- **Do not** modify README or ai-prompts
- **Do not** commit or push
- Provide files changed, architecture, decisions, Databricks steps; stop for review

### Outcome

- Created full `src/silver/` package
- Updated `src/config.py`, `database/schema.sql`
- Bronze unchanged

---

## Prompt 11 — Fix Silver uniqueness window function

### User request (summary)

Fix Databricks error `WINDOW_FUNCTION_NOT_ALLOWED_IN_CLAUSE`:

- **Do not** use `df.filter(F.count("*").over(window) > 1)`
- Materialize `_duplicate_count` column first, then `duplicate_condition = col("_duplicate_count") > 1`
- Drop `_duplicate_count` before writing Silver table
- Review entire Silver for other window-in-WHERE cases
- Minimal fix; **do not** modify Bronze or Silver architecture

### Outcome

- **File changed:** `src/silver/02_quality_uniqueness.py` only
- Grep confirmed no other window-in-filter usage in Silver

---

## Prompt 12 — Master prompt history (this file)

### User request

> please document all my prompts , my requests in a new file in ai-prompts and capture every detail i asked u properly , like prompt history, do quickly

### Intent

Single comprehensive prompt-history document covering every user request in the project.

### Outcome

This file (`09-complete-prompt-history.md`).

---

## Cross-cutting rules the user repeated

| Rule | Appeared in |
|------|-------------|
| Do not modify `docs/assignment.md` unless asked | Project rules + early prompts |
| Do not invent requirements | Analysis + all implementation prompts |
| Bronze = raw ingest, no cleaning | Prompts 4, 5, 8 |
| Silver = flag, don't delete | Prompts 9, 10 |
| Don't commit/push unless asked | Prompts 7, 10, 12 |
| Don't modify README/ai-prompts unless asked | Prompts 10 (Silver impl) |
| Follow existing Bronze patterns for new layers | Prompts 8, 9, 10 |
| Unity Catalog: `workspace.bronze`, `workspace.silver` | Prompts 8, 9, 10 |
| Volume path: `/Volumes/workspace/default/st-de-medallion-data` | Prompts 7, 8 |

---

## Project timeline (high level)

```
01–03  Requirements + architecture (analysis only)
04     Sample data generation (+ integer CSV fix)
05–06  Bronze implementation + read-path review
07–08  Bronze Databricks execution + troubleshooting docs
08b    Unity Catalog Volume Bronze config
09     Silver analysis (plan only)
10     Silver implementation
11     Silver uniqueness window fix
12     This master prompt history
```

---

## Branches mentioned

| Branch | Work |
|--------|------|
| `feature/bronze-layer` | Bronze implementation, UC Volume, merged to master |
| `feature/silver-layer` | Silver analysis + implementation + uniqueness fix |

---

## Execution environments documented

| Environment | Config |
|-------------|--------|
| Local | `DATA_PATH=<repo>/data`, `BRONZE_SCHEMA=bronze`, `SILVER_SCHEMA=silver` |
| Databricks | `DATA_PATH=/Volumes/workspace/default/st-de-medallion-data`, `BRONZE_SCHEMA=workspace.bronze`, `SILVER_SCHEMA=workspace.silver` |
| Databricks notebook | `sys.path` + `from src.bronze.ingest_all import main` or `from src.silver.create_silver_tables import main` |

---

## Intentional data quality defects (reference)

| File | Defect | Count | Silver detection |
|------|--------|-------|------------------|
| customers | NULL email | 50 | `COMPLETENESS_EMAIL` |
| customers | Duplicate customer_id | 10 keys | `UNIQUENESS_CUSTOMER_ID` |
| orders | NULL customer_id | 100 | `COMPLETENESS_CUSTOMER_ID` |
| orders | NULL product_id | 200 | `COMPLETENESS_PRODUCT_ID` |
| orders | Orphan customer_id | 50 | `RI_CUSTOMER` |
| orders | Orphan product_id | 30 | `RI_PRODUCT` |
| orders | Duplicate order_id | 20 keys | `UNIQUENESS_ORDER_ID` |
| products | None | 0 | — |

---

## Related documentation (not prompt history)

- `docs/assignment.md` — authoritative spec
- `design-notes.md`, `data-model.md`, `data-quality-strategy.md` — design artifacts
- `README.md` — pipeline status and quick start
