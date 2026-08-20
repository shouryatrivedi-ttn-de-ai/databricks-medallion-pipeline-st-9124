# Databricks Medallion Pipeline

E-commerce data pipeline implementing Bronze → Silver → Gold → Dashboard on Databricks.

**Repository:** `databricks-medallion-pipeline-st-9124`  
**Current branch:** `feature/bronze-layer`

## Pipeline Status

| Layer | Status |
|-------|--------|
| Sample data generation | Complete — CSVs in `data/` with intentional quality defects |
| Bronze | **Complete and validated on Databricks** |
| Silver | Not started |
| Gold | Not started |
| Dashboard | Not started |

### Bronze layer (executed)

Bronze ingestion has been successfully executed on Databricks against source CSVs in Unity Catalog Volume `/Volumes/workspace/default/st-de-medallion-data`, writing Delta tables to `workspace.bronze` with all validation checks passing (exit code 0).

See `ai-prompts/07-bronze-databricks-execution-and-troubleshooting.md` for the full execution journey.

## Quick Start

### Generate sample data (local)

```powershell
pip install -r requirements.txt
python src/data_generation/generate_sample_data.py
```

### Run Bronze locally

```powershell
$env:BRONZE_SCHEMA = "bronze"
python src/bronze/ingest_all.py
```

### Run Bronze on Databricks

Set environment variables and import the orchestrator from the Git folder. See `ai-prompts/07-bronze-databricks-execution-and-troubleshooting.md` for notebook setup and troubleshooting.

## Documentation

- `docs/assignment.md` — assignment specification
- `design-notes.md` — architecture and design decisions
- `ai-prompts/` — AI-assisted development prompt history
