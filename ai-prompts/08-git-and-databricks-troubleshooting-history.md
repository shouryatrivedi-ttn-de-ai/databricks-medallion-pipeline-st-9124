# Git and Databricks Troubleshooting Reference

## Purpose

Concise troubleshooting history for Bronze layer deployment on Databricks. For full execution context, see `07-bronze-databricks-execution-and-troubleshooting.md`.

**Repository:** `databricks-medallion-pipeline-st-9124`  
**Branch:** `feature/bronze-layer`

---

## Git Authentication Issues

### Symptoms

- Authentication needed for cloning
- Invalid authorization state
- Could not read remote repository

### Repository URL

```
https://github.com/shouryatrivedi-ttn-de-ai/databricks-medallion-pipeline-st-9124.git
```

### Resolution

Updated/configured GitHub credentials with appropriate repository access. After credential resolution, the repository became visible in the Databricks Workspace.

---

## Bronze Folder Not Appearing Initially

### Symptom

`src/bronze/` was not visible in the Databricks Git folder after initial setup attempts.

### Resolution

Resolved once Git authentication succeeded and the repository synced correctly. Expected Bronze files:

```
src/bronze/
├── 01_ingest_customers.py
├── 02_ingest_orders.py
├── 03_ingest_products.py
├── ingest_all.py
├── ingest_utils.py
├── schemas.py
└── validate_bronze.py
```

---

## Wrong `%run` Path / Notebook vs Python File

### Symptom

```
Notebook not found:
Users/shourya.trivedi@tothenew.com/src/bronze/ingest_all
```

### Cause

- Notebook `run_bronze_ingestion` was outside the repository path
- `%run ./src/bronze/ingest_all` targeted a **Python source file**, not a Databricks notebook
- `%run` resolves notebook paths, not `.py` modules in a Git folder

### Fix

Import the Python module by adding the repo root to `sys.path`:

```python
import sys

repo_root = "/Workspace/Users/shourya.trivedi@tothenew.com/databricks-medallion-pipeline-st-9124"

if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.bronze.ingest_all import main

exit_code = main()
```

Set environment variables before calling `main()`:

```python
import os

os.environ["DATA_PATH"] = "/Volumes/workspace/default/st-de-medallion-data"
os.environ["BRONZE_SCHEMA"] = "workspace.bronze"
```

---

## Pushing to Wrong Branch

### Symptom

```bash
git push origin main
```

**Error:**

```
src refspec main does not match any
```

### Cause

Current branch was `feature/bronze-layer`, not `main`.

### Fix

Confirm active branch:

```bash
git branch --show-current
# feature/bronze-layer
```

Push to the correct branch:

```bash
git push origin feature/bronze-layer
```

**Result:** `feature/bronze-layer -> feature/bronze-layer` (successful)

---

## Terminal Typo

### Symptom

PowerShell error when running:

```
it push origin feature/bronze-layer
```

### Cause

Missing leading `g` — `it` is not `git`. PowerShell interpreted `it` as a different command and produced a parameter transformation error.

### Fix

Use the full command:

```bash
git push origin feature/bronze-layer
```

---

## Quick Reference

| Issue | Correct action |
|-------|----------------|
| Git clone/auth failure | Configure GitHub credentials with repo access |
| Bronze folder missing | Re-sync Git folder after auth fix |
| `%run` on `.py` file | Use `sys.path` + `from src.bronze.ingest_all import main` |
| Push to `main` fails | Push to `feature/bronze-layer` instead |
| Terminal typo | Use `git`, not `it` |
