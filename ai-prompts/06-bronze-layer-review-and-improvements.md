# AI Prompt 06 — Bronze Layer Review and Improvements

## Purpose / Context

After the initial Bronze implementation, the ingestion read path was reviewed before running the layer against the generated CSVs.

The concern was whether Bronze truly preserved source data or could silently alter values during ingest — especially malformed values that might be converted to NULL and later mistaken for intentional completeness defects in Silver.

## Prompt Sent

Review the Bronze ingestion implementation, especially the read_csv_raw and cast_to_schema flow.

Bronze should preserve source data and should not silently convert malformed source values into NULL because of a later cast.

Simplify the ingestion so the CSV is read using the entity's explicit Spark schema directly where possible, while preserving the intentional NULLs, duplicates and orphan IDs required for later Silver validation.

Remove unnecessary transformation logic if it does not belong in Bronze.

Keep the ingestion metadata, Delta writes, ingestion log and validation structure unchanged.

Do not implement any Silver logic.

## Initial Approach (Before Review)

The first Bronze implementation used a two-step read path in `ingest_utils.py`:

1. **`read_csv_raw()`** — read all CSV columns as strings
2. **`cast_to_schema()`** — manually cast each column to the explicit Bronze schema

Empty strings were converted to NULL, then remaining values were cast to typed columns.

## Problem Identified

Spark `cast()` failures do not raise errors by default — they produce **NULL**.

That meant a malformed source value (for example an unparseable integer) could silently become NULL during Bronze ingest. In Silver, that could be indistinguishable from an **intentional** NULL `customer_id` or `product_id` completeness defect.

This violated the Bronze principle of preserving source data faithfully.

## Improved Approach

Bronze ingest was simplified to a single-step read:

```python
spark.read.schema(schema)
  .option("header", True)
  .option("nullValue", "")       # empty CSV fields → NULL
  .option("dateFormat", "yyyy-MM-dd")
  .option("mode", "FAILFAST")    # malformed values fail ingest, not silent NULL
  .csv(source_path)
```

### What changed

| Before | After |
|--------|-------|
| String read + manual cast | Direct explicit schema read |
| Cast failures → silent NULL | FAILFAST on parse errors |
| Extra transformation step | Read → metadata → Delta write |

### What stayed the same

- `_ingest_timestamp` and `_source_file` metadata
- Delta table writes (`overwrite`)
- `bronze.ingestion_log` append logic
- Bronze validation (row counts, metadata checks)
- Orchestrator and per-table scripts

### Why FAILFAST is safer

- **Intentional NULLs** still work via `nullValue=""` on empty CSV fields.
- **Duplicates and orphan IDs** are valid typed values and read normally.
- **Malformed values** fail the job loudly instead of disappearing as NULL.
- Silver can trust that NULLs in Bronze came from the source CSV, not from a failed cast during ingest.

## Follow-On Issue — Integer CSV Formatting

When switching to direct schema reading, another issue surfaced: the generated `orders.csv` contained pandas-style integer formatting such as `2529.0` instead of `2529`.

This happened because pandas promotes integer columns to float when NULLs are present, and the original CSV export wrote those float-formatted values.

With direct `IntegerType` schema reading and `FAILFAST`, those values could cause ingest failures rather than silent NULL conversion — which is the correct behavior for surfacing a format problem, but it blocked a clean Bronze run.

### Follow-Up Prompt Sent

Before we run the Bronze layer, fix the data generator so integer columns are written to the CSV as integers without pandas-style values such as 2529.0.

This should only address CSV output formatting caused by nullable integer columns. Do not change the generated row counts, intentional defect counts, random seed, or the data-quality scenarios.

After the change, regenerate the CSV files and run the existing data-generation validation again.

Do not modify Bronze, Silver, Gold, or dashboard code.

### Outcome

`write_csv()` in `generate_sample_data.py` was updated to export integer columns using pandas nullable `Int64`, producing values like `2529` instead of `2529.0`. CSVs were regenerated and all defect-count validations passed again.

This was a **CSV export formatting fix**, not a change to generated data scenarios. It aligned the source files with the explicit Bronze integer schemas.

## What I Accepted

- Removing the string-read + manual-cast pattern from Bronze.
- Direct explicit schema CSV reading.
- `FAILFAST` mode to prevent silent NULL conversion on parse errors.
- Fixing integer CSV export in the data generator as a separate, scoped follow-up.

## What I Changed

- Bronze read path simplified from two steps to one.
- Data generator CSV export updated after the review revealed the `2529.0` formatting issue.

## What I Rejected

- Keeping manual post-read casting in Bronze (too risky for silent data loss).
- Fixing the issue by coercing malformed values during Bronze ingest (that would be cleaning/transforming source data).

## Why

Bronze should be a faithful raw landing zone. Silent cast-to-NULL is a hidden transformation that undermines downstream quality testing.

Direct schema reading with FAILFAST makes parse problems visible. The integer CSV export fix ensures the source files match the declared schema without changing the intentional defect scenarios.

## Validation

- Bronze ingest logic reviewed: unnecessary cast step removed.
- Ingest metadata, Delta writes, ingestion log, and validation structure confirmed unchanged.
- Data generator CSVs regenerated after integer export fix; all seven defect-count checks passed.
- CSV integer columns verified to export without `.0` suffix (for example `2529` not `2529.0`).
