# AI Prompt 04 — Sample Data Generation

## Purpose / Context

After completing the requirements analysis and architecture design, the next step was to implement the sample data generator under `src/data_generation/`.

The assignment requires three CSV source files with realistic volumes and intentional data-quality defects that the Silver layer will later detect. The generator needed to be reproducible, modular, and able to validate that the expected defect counts were actually created.

## Prompt Sent

Let's start implementing the sample data generator.

Create the data generation code under `src/data_generation/`.

Use Python with Faker/pandas where useful and make the generation deterministic with a fixed random seed.

Generate the three CSVs required by the assignment:
- customers.csv
- orders.csv
- products.csv

Please include the intentional data-quality issues specified in the assignment, rather than generating perfectly clean data.

I also want the generator to validate itself after generation so we can confirm the expected number of intentional defects were actually created.

Keep the generator modular and readable. Don't start implementing Bronze, Silver, Gold or dashboard code yet.

After implementing it, explain the files you created and how I should run the generator and validate the results.

## AI Response Summary

Cursor created a modular sample data generator under `src/data_generation/`:

- `config.py` — seed, row counts, defect counts, output paths
- `generators/products.py`, `generators/customers.py`, `generators/orders.py` — entity generation and defect injection
- `validation.py` — post-generation defect count checks
- `generate_sample_data.py` — orchestrator entry point
- `DATA_GENERATION_NOTES.md` — seed, defect design, counting notes

Generation order was products → customers → orders. A fixed random seed (`42`) was used for reproducibility.

## Key Decisions / Outcomes

### Row volumes

| File | Rows |
|------|------|
| customers.csv | 10,000 |
| products.csv | 500 |
| orders.csv | 100,000 |

### Intentional defects injected

| File | Defect | Count |
|------|--------|-------|
| customers.csv | NULL `email` | 50 |
| customers.csv | Duplicate `customer_id` keys | 10 |
| orders.csv | NULL `customer_id` | 100 |
| orders.csv | NULL `product_id` | 200 |
| orders.csv | Orphan `customer_id` | 50 |
| orders.csv | Orphan `product_id` | 30 |
| orders.csv | Duplicate `order_id` keys | 20 |
| products.csv | None | 0 |

Orphan foreign keys use IDs starting at `900001`, outside valid parent ranges. NULL FK and orphan FK injections use disjoint row sets so each defect type is independently countable.

### Self-validation

After writing CSVs, the generator runs validation checks and prints PASS/FAIL for each expected defect count. Exit code `0` means all checks passed.

Initial validation result: **ALL CHECKS PASSED** (460 defect markers counted across the seven checks).

## Follow-Up Prompt — Integer CSV Formatting

Before running Bronze ingestion, we noticed that nullable integer columns in `orders.csv` were exported with pandas-style float formatting, for example `2529.0` instead of `2529`.

### Prompt Sent

Before we run the Bronze layer, fix the data generator so integer columns are written to the CSV as integers without pandas-style values such as 2529.0.

This should only address CSV output formatting caused by nullable integer columns. Do not change the generated row counts, intentional defect counts, random seed, or the data-quality scenarios.

After the change, regenerate the CSV files and run the existing data-generation validation again.

Do not modify Bronze, Silver, Gold, or dashboard code.

### Outcome

`write_csv()` in `generate_sample_data.py` was updated to convert integer columns (`customer_id`, `order_id`, `product_id`, `quantity`, `stock_quantity`, `reorder_level`) to pandas nullable `Int64` before export. This only changed CSV formatting at write time; generation logic and defect injection were unchanged.

CSVs were regenerated and all defect-count validations passed again.

## What I Accepted

- Modular generator structure under `src/data_generation/`.
- Fixed seed (`42`) for reproducibility.
- Exact assignment defect counts with post-generation validation.
- Generation order: products → customers → orders.
- Separate `validation.py` module for defect count assertions.
- Later CSV export fix for integer formatting without changing data scenarios.

## What I Changed

- Asked for the integer CSV export fix once Bronze direct schema reading highlighted the `2529.0` formatting issue.
- No changes to defect counts, seed, or generation logic after the initial implementation.

## What I Rejected

- Generating perfectly clean data (assignment requires intentional defects).
- Starting Bronze/Silver/Gold/dashboard work in the same step.

## Why

The sample data is the foundation for Silver-layer quality testing. Defect counts must be exact and reproducible so later pipeline tests can prove the quality checks work.

The integer export fix was needed so CSV values match the declared integer schema during Bronze ingest, without changing the underlying generated data.

## Validation

- Generator ran successfully and wrote all three CSVs to `data/`.
- All seven defect-count checks passed before and after the integer export fix.
- Row counts confirmed: 10,000 customers, 500 products, 100,000 orders.
