# AI Prompt 07 — Bronze Databricks Execution and Troubleshooting

## Purpose / Context

This document records the end-to-end Bronze layer execution on Databricks after the implementation and review work documented in:

- `05-bronze-layer-implementation.md` — initial Bronze design and code structure
- `06-bronze-layer-review-and-improvements.md` — read-path review, FAILFAST, and CSV integer export fix

Those earlier prompts cover **how Bronze was built**. This prompt covers **how Bronze was deployed, executed, validated, and troubleshooted on Databricks**.

**Repository:** `databricks-medallion-pipeline-st-9124`  
**Branch:** `feature/bronze-layer`  
**Remote:** `origin/feature/bronze-layer` (up to date at time of documentation)

---

## Objective

Execute the existing Bronze ingestion pipeline on Databricks against CSV source files stored in a Unity Catalog Volume, write Delta tables under `workspace.bronze`, validate row counts and ingestion metadata, and preserve the implementation journey for future reference.

---

## Architecture

### Source data (Unity Catalog Volume)

```
/Volumes/workspace/default/st-de-medallion-data
├── customers.csv   (10,000 rows)
├── orders.csv      (100,000 rows)
└── products.csv    (500 rows)
```

### Bronze target (Unity Catalog)

**Schema:** `workspace.bronze`

**Delta tables:**

| Table | Expected rows |
|-------|---------------|
| `workspace.bronze.products` | 500 |
| `workspace.bronze.customers` | 10,000 |
| `workspace.bronze.orders` | 100,000 |
| `workspace.bronze.ingestion_log` | audit entries per entity |

### Technology stack

- PySpark
- Delta Lake
- Databricks
- Unity Catalog
- Unity Catalog Volumes
- Explicit Spark schemas
- Environment-variable configuration
- Git version control (Databricks Git folder)

---

## Repository Structure (Bronze)

```
src/bronze/
├── 01_ingest_customers.py
├── 02_ingest_orders.py
├── 03_ingest_products.py
├── __init__.py
├── ingest_all.py          # orchestrator
├── ingest_utils.py        # shared ingest logic
├── schemas.py             # explicit Spark schemas
└── validate_bronze.py     # post-ingest validation
```

Shared configuration: `src/config.py`

---

## Configuration Strategy

`src/config.py` uses environment variables so the same codebase runs locally and on Databricks.

| Setting | Local default | Databricks override |
|---------|---------------|-------------------|
| `DATA_PATH` | `<repo>/data` | `/Volumes/workspace/default/st-de-medallion-data` |
| `BRONZE_SCHEMA` | `workspace.bronze` | `workspace.bronze` (default; can override) |
| `BRONZE_WRITE_MODE` | `overwrite` | configurable |

Local Spark without Unity Catalog can override:

```powershell
$env:BRONZE_SCHEMA = "bronze"
```

Databricks notebook configuration used at execution time:

```python
import os

os.environ["DATA_PATH"] = "/Volumes/workspace/default/st-de-medallion-data"
os.environ["BRONZE_SCHEMA"] = "workspace.bronze"
```

Expected row counts and CSV mapping remain defined in `src/config.py`:

- `customers` → `customers.csv` → 10,000
- `orders` → `orders.csv` → 100,000
- `products` → `products.csv` → 500

Ingestion metadata columns added at Bronze:

- `_ingest_timestamp`
- `_source_file`

---

## Unity Catalog Volume Support

To support both local filesystem paths and Databricks Volumes, `resolve_csv_path()` in `src/bronze/ingest_utils.py` was updated:

**Databricks Volume paths** (`DATA_PATH` starts with `/Volumes/`):

```python
return f"{DATA_PATH.rstrip('/')}/{filename}"
```

No `Path.exists()` or `Path.stat()` checks are performed for Volume paths (not valid locally).

**Local paths** retain pathlib validation:

- file must exist
- file must not be empty
- return resolved absolute path

This allows one codebase to run in both environments without hardcoding the Volume path as the default `DATA_PATH`.

---

## Bronze Ingestion Flow

**Orchestrator:** `src/bronze/ingest_all.py`

**Ingest order:** products → customers → orders (parents before child for traceability)

**Steps:**

1. Create/reuse SparkSession (`get_spark()`)
2. Ensure Bronze schema exists (`ensure_bronze_schema()` → `CREATE SCHEMA IF NOT EXISTS workspace.bronze`)
3. Ingest products
4. Ingest customers
5. Ingest orders
6. Run Bronze validation (`validate_bronze.py`)
7. Return exit code `0` if all checks pass, `1` if any fail

### Per-entity ingest (`ingest_entity()`)

1. Resolve CSV path (`resolve_csv_path()`)
2. Read CSV with explicit schema (`read_csv_with_schema()`)
   - `header=True`
   - `nullValue=""`
   - `dateFormat="yyyy-MM-dd"`
   - `mode="FAILFAST"` (malformed values fail ingest, not silent NULL)
3. Add metadata (`add_ingest_metadata()`)
4. Write Delta table (`write_delta_table()`, mode from `BRONZE_WRITE_MODE`)
5. Append to `workspace.bronze.ingestion_log`

### Ingestion log fields

- `entity`
- `row_count`
- `source_path`
- `ingest_timestamp`

---

## Databricks Git Integration

The repository was connected to Databricks as a Git folder:

```
https://github.com/shouryatrivedi-ttn-de-ai/databricks-medallion-pipeline-st-9124.git
```

After successful authentication and sync, the Bronze source folder appeared under the Databricks Git checkout:

```
src/bronze/
```

See `08-git-and-databricks-troubleshooting-history.md` for authentication and Git troubleshooting details.

---

## Authentication Issues and Resolution

Initial Git clone/sync attempts failed with errors including:

- Authentication needed for cloning
- Invalid authorization state
- Could not read remote repository

**Resolution:** GitHub credentials were updated/configured with appropriate repository access. After that, the repository became visible in the Databricks Workspace and the Bronze folder synced correctly.

---

## Python Script Execution from Databricks Notebook

**Notebook created:** `run_bronze_ingestion`

### Failed approach: `%run` on a `.py` file outside repo context

Initial attempt:

```
%run ./src/bronze/ingest_all
```

**Why it failed:**

- The notebook was outside the repository path context
- `%run` targets Databricks notebooks, not plain Python source files

**Error:**

```
Notebook not found:
Users/shourya.trivedi@tothenew.com/src/bronze/ingest_all
```

### Working approach: module import via `sys.path`

Add the repository root to `sys.path`, then import and call `main()`:

```python
import os
import sys

os.environ["DATA_PATH"] = "/Volumes/workspace/default/st-de-medallion-data"
os.environ["BRONZE_SCHEMA"] = "workspace.bronze"

repo_root = "/Workspace/Users/shourya.trivedi@tothenew.com/databricks-medallion-pipeline-st-9124"

if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.bronze.ingest_all import main

exit_code = main()
print(f"Ingestion finished with exit code: {exit_code}")
```

---

## Successful Pipeline Execution

Bronze ingestion completed successfully on Databricks.

| Entity | Source | Target | Rows ingested |
|--------|--------|--------|---------------|
| products | `/Volumes/workspace/default/st-de-medallion-data/products.csv` | `workspace.bronze.products` | 500 |
| customers | `/Volumes/workspace/default/st-de-medallion-data/customers.csv` | `workspace.bronze.customers` | 10,000 |
| orders | `/Volumes/workspace/default/st-de-medallion-data/orders.csv` | `workspace.bronze.orders` | 100,000 |

---

## Validation Results

All Bronze validation checks passed:

```
[PASS] customers.row_count
[PASS] customers.metadata
[PASS] orders.row_count
[PASS] orders.metadata
[PASS] products.row_count
[PASS] products.metadata
[PASS] ingestion_log.entity.customers
[PASS] ingestion_log.entity.orders
[PASS] ingestion_log.entity.products

Overall: ALL CHECKS PASSED
Ingestion finished with exit code: 0
```

---

## Git Branch and Push Troubleshooting

Bronze work lives on branch `feature/bronze-layer`.

**Relevant commit history (recent):**

| Commit | Description |
|--------|-------------|
| `80aec9e` | Add Bronze ingestion pipeline |
| `869ad45` | Support Unity Catalog Volume for Bronze ingestion |
| `1900a27` | Add Bronze ingestion and validation layer |
| `ed1751b` | Initial project setup and sample data generation |

**Wrong push attempt:**

```bash
git push origin main
```

**Error:** `src refspec main does not match any` (current branch was not `main`)

**Correct push:**

```bash
git push origin feature/bronze-layer
```

**Final Git status at documentation time:**

```
On branch feature/bronze-layer
Your branch is up to date with 'origin/feature/bronze-layer'.
nothing to commit, working tree clean
```

See `08-git-and-databricks-troubleshooting-history.md` for a concise troubleshooting reference.

---

## Final State

- Bronze implementation complete and pushed to `feature/bronze-layer`
- Source CSVs ingested from Unity Catalog Volume
- Delta tables created under `workspace.bronze`
- Ingestion log populated
- All validation checks passed (exit code 0)
- Working tree clean; branch up to date with remote

---

## Key Learnings

1. **Environment-based config** keeps one codebase portable across local and Databricks without hardcoding Volume paths.
2. **Volume path handling** must skip local filesystem checks (`Path.exists()`) for `/Volumes/` paths.
3. **`%run` is for Databricks notebooks**, not `.py` source files — use `sys.path` + module import for Git-folder Python scripts.
4. **FAILFAST CSV reading** (from the earlier review in prompt 06) ensures Bronze does not silently convert malformed values to NULL.
5. **Unity Catalog three-part names** (`workspace.bronze.customers`) work with the existing `f"{BRONZE_SCHEMA}.{entity}"` table naming pattern.
6. **Validate after ingest** — row counts and metadata checks confirmed the pipeline ran correctly end-to-end.
7. **Push to the active branch** — verify with `git branch --show-current` before pushing.

---

## Related Documentation

| File | Topic |
|------|-------|
| `04-sample-data-generation.md` | Sample CSV generation and defect validation |
| `05-bronze-layer-implementation.md` | Initial Bronze code structure |
| `06-bronze-layer-review-and-improvements.md` | Read-path review and FAILFAST |
| `08-git-and-databricks-troubleshooting-history.md` | Concise troubleshooting reference |
