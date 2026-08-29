# Complete Project Prompt History

> Master index of AI-assisted development across the Databricks Medallion pipeline project.  
> Detailed stage documentation lives in numbered files `01`-`12`.

**Repository:** `databricks-medallion-pipeline-st-9124`  
**Last updated:** After prompt-history completion and encoding review (Prompt 22)

---

## Numbering convention

| Term | Meaning |
|------|---------|
| **File number** (`01`-`12`) | Prefix on `ai-prompts/*.md` stage documents |
| **Global prompt number** (`1`-`22`) | Chronological user request sequence in this index |
| **Verbatim** | Prompt text preserved in an earlier file or in this index from the original session |
| **Reconstructed** | Summarized from git history, code, or development sessions; exact wording not in repo |

**Note:** Global Prompt 12 in the original `09` draft meant "create this master history file." The index below extends global numbering through Prompt 22 for later phases.

---

## How to use this file

This file is a **chronological index and summary**. For full detail on a stage, read the linked file.

| File | Covers |
|------|--------|
| `01-requirements-analysis.md` | Initial requirements analysis |
| `02-refine-requirements.md` | Silver four-check working decision |
| `03-architecture-design.md` | CSV -> Bronze -> Silver -> Gold design |
| `04-sample-data-generation.md` | Sample data generator + integer CSV fix |
| `05-bronze-layer-implementation.md` | Bronze layer code |
| `06-bronze-layer-review-and-improvements.md` | Bronze read-path review, FAILFAST |
| `07-bronze-databricks-execution-and-troubleshooting.md` | Databricks Bronze execution |
| `08-git-and-databricks-troubleshooting-history.md` | Git/auth/%run troubleshooting |
| `09-complete-prompt-history.md` | **This file** - master index |
| `10-silver-layer-implementation.md` | Silver DQ implementation + uniqueness fix |
| `11-gold-layer-and-dashboard.md` | Gold aggregations, validation, dashboard |
| `12-final-project-polish.md` | README, gap analysis, dashboard alignment, portfolio polish |

---

## Chronological timeline

```
Phase 1 - Planning (01-03)
  Requirements analysis, Silver check interpretation, architecture design

Phase 2 - Sample data (04)
  Generator, intentional defects, integer CSV fix

Phase 3 - Bronze (05-08)
  Implementation, read-path review, Databricks execution, Git troubleshooting
  Branch: feature/bronze-layer -> merged to master (PR #1)

Phase 4 - Silver (09-11 in this file; detail in 10)
  Analysis, implementation, uniqueness window fix
  Branch: feature/silver-layer

Phase 5 - Gold (detail in 11)
  Aggregations, eligibility, validation baseline fix
  Branch: feature/gold-layer -> merged to master (PR #2)

Phase 6 - Dashboard (detail in 11)
  Initial SQL/guide, alignment with deployed four-tile dashboard

Phase 7 - Portfolio polish (detail in 12)
  Gap analysis, README rewrite, dashboard doc alignment, prompt-history completion
  Branch: master
```

---

## Phase 1-3 summary (Bronze and earlier)

Detailed prompts 1-8 are documented inline below and in files `01`-`08`.

| # | Topic | Detail file |
|---|-------|-------------|
| 1 | Session start | - |
| 2 | Sample data generator | `04` |
| 3 | Explain data generator (educational) | - |
| 4 | Implement Bronze layer | `05` |
| 5 | Review/fix Bronze read path | `06` |
| 6 | Fix integer CSV export | `04` |
| 7 | Document Bronze Databricks journey | `07`, `08` |
| 8 | Adapt Bronze for Unity Catalog Volume | `07` |

---

## Phase 4 - Silver (Prompts 9-11)

**Detail:** `10-silver-layer-implementation.md`

| # | Topic | Git / outcome |
|---|-------|---------------|
| 9 | Silver analysis only (no code) | Plan: four checks, flag-don't-delete, `workspace.silver` |
| 10 | Implement Silver layer | `212ffc6` - full `src/silver/` package |
| 11 | Fix uniqueness window function | `720ffee` - `02_quality_uniqueness.py` only |

**Active checks:** completeness, uniqueness, type validation, referential integrity  
**Stub (not wired):** `05_quality_business_logic.py`  
**Validation:** `validate_silver.py` - row retention, defect minimums, quality_metrics

---

## Phase 5 - Gold (Prompts 12-14, reconstructed)

> **Reconstructed:** Prompt summaries below are inferred from git commits and code; verbatim user prompts are not stored in the repository.

**Detail:** `11-gold-layer-and-dashboard.md`

| # | Topic | Git / outcome |
|---|-------|---------------|
| 12 | Implement Gold layer | `58ffdee` - SQL aggregations, eligibility, orchestrator |
| 13 | Fix Gold validation baselines | `68b8bc9` - customer-attributed baselines, valid_labels fix |
| 14 | Gold execution on Databricks | User-reported: validated (no dedicated execution doc in ai-prompts) |

**Gold tables:** `sales_by_product`, `revenue_by_customer`, `customer_segmentation`  
**Not implemented:** `03_daily_weekly_trends.sql` (optional stretch)

---

## Phase 6 - Dashboard (Prompts 15-18, reconstructed)

> **Reconstructed:** Prompt summaries below are inferred from git commits and development sessions.

**Detail:** `11-gold-layer-and-dashboard.md`

| # | Topic | Git / outcome |
|---|-------|---------------|
| 15 | Initial dashboard SQL + guide | `27dcb37` - assignment-style three-tile queries |
| 16 | Dashboard review and alignment | Analysis: filters required, SQL/guide mismatch with deployed UI |
| 17 | Align dashboard_queries.sql | `f3d8519` - QUERY 1-4 for deployed four tiles |
| 18 | Align DASHBOARD_GUIDE.md | `ae8922d` - four-tile guide |

**Deployed dashboard tiles:**

1. Customer Distribution by Segment (pie/donut)
2. Total Revenue by Customer Segment (bar)
3. Top 10 Customers by Revenue (bar)
4. Total Revenue by Product Category (bar)

---

## Phase 7 - Portfolio polish (Prompts 19-22, reconstructed)

> **Reconstructed:** Prompt summaries below are inferred from polish-phase development sessions.

**Detail:** `12-final-project-polish.md`

| # | Topic | Outcome |
|---|-------|---------|
| 19 | Strict gap analysis (analysis only) | ~73% mandatory completion; dashboard/docs gaps identified |
| 20 | Portfolio README rewrite | Full README with Mermaid, all layers, dashboard |
| 21 | Dashboard query/guide alignment | Commits `f3d8519`, `ae8922d` |
| 22 | Complete ai-prompts history + encoding review | Files `10`, `11`, `12`; this index updated; ASCII normalization |

---

## Early prompts (1-8) - condensed detail

### Prompt 1 - Greeting / session start

Session opener before implementation work.

### Prompt 2 - Implement sample data generator

- 10K customers, 100K orders, 500 products, seed 42
- Seven intentional defect types, self-validation
- **See:** `04-sample-data-generation.md`

### Prompt 3 - Explain data generator (educational)

Conceptual explanation only - no code changes.

### Prompt 4 - Implement Bronze layer

- Raw ingest, metadata, explicit schemas, validation
- **See:** `05-bronze-layer-implementation.md`

### Prompt 5 - Review and fix Bronze read path

- FAILFAST direct schema read; removed string cast path
- **See:** `06-bronze-layer-review-and-improvements.md`

### Prompt 6 - Fix integer CSV export

- pandas nullable `Int64` for integer columns in CSV output
- **See:** `04-sample-data-generation.md`

### Prompt 7 - Document Bronze journey

- Created `07`, `08`, minimal README Bronze status
- **See:** `07-bronze-databricks-execution-and-troubleshooting.md`

### Prompt 8 - Adapt Bronze for Unity Catalog Volume

- `BRONZE_SCHEMA=workspace.bronze`, Volume path without `Path.exists()`
- **See:** `07-bronze-databricks-execution-and-troubleshooting.md`

---

## Cross-cutting rules the user repeated

| Rule | Appeared in |
|------|-------------|
| Do not modify `docs/assignment.md` unless asked | Project rules + early prompts |
| Do not invent requirements | Analysis + all implementation prompts |
| Bronze = raw ingest, no cleaning | Prompts 4, 5, 8 |
| Silver = flag, don't delete | Prompts 9, 10 |
| Don't commit/push unless asked | Multiple prompts |
| Don't modify pipeline code during doc-only tasks | Polish phase (12) |
| Unity Catalog: `workspace.bronze`, `workspace.silver`, `workspace.gold` | Prompts 8-11 |
| Volume path: `/Volumes/workspace/default/st-de-medallion-data` | Prompts 7, 8 |

---

## Branches

| Branch | Work | Status |
|--------|------|--------|
| `feature/bronze-layer` | Bronze, UC Volume, execution docs | Merged to `master` (PR #1) |
| `feature/silver-layer` | Silver analysis, implementation, uniqueness fix | Commits on branch |
| `feature/gold-layer` | Gold, dashboard, validation fix | Merged to `master` (PR #2) |
| `master` | Dashboard doc alignment, README polish | Current integration branch |

---

## Execution environments

| Environment | Config |
|-------------|--------|
| Local data gen | `python src/data_generation/generate_sample_data.py` |
| Local Bronze | `DATA_PATH=<repo>/data`, `BRONZE_SCHEMA=bronze` |
| Databricks | `DATA_PATH=/Volumes/workspace/default/st-de-medallion-data`, `BRONZE_SCHEMA=workspace.bronze`, `SILVER_SCHEMA=workspace.silver`, `GOLD_SCHEMA=workspace.gold` |
| Databricks notebook | `sys.path` + `from src.<layer>.<orchestrator> import main` |

**Documentation gap:** Bronze execution is fully documented in `07`. Silver and Gold Databricks execution rely on README and user-reported validation - not recreated here.

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
| products | None | 0 | - |

---

## Historical gaps (honest)

| Gap | Notes |
|-----|-------|
| Gold/Dashboard prompt wording | Reconstructed from git commits and development sessions; exact user prompt text not always in repo |
| Silver/Gold Databricks execution logs | Not stored in ai-prompts (unlike Bronze `07`) |
| Dashboard UI screenshots | Not in repository |
| Assignment submission artifacts | `reflection.md`, `tool-workflow.md`, etc. not created in documented phases |
| Prompt numbering in this file | Global prompts 12-21 cover Gold, Dashboard, and polish; original `09` draft ended at meta-Prompt 12 ("create master history") |

---

## Related documentation (not prompt history)

| File | Purpose |
|------|---------|
| `docs/assignment.md` | Authoritative specification |
| `README.md` | Portfolio-facing project overview |
| `design-notes.md`, `data-model.md`, `data-quality-strategy.md` | Design artifacts |
| `src/dashboard/DASHBOARD_GUIDE.md` | Dashboard setup |
| `src/dashboard/dashboard_queries.sql` | QUERY 1-4 SQL |
