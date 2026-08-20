# Data Generation Notes

## Overview

Sample CSVs are produced by `generate_sample_data.py` using Python, pandas, and Faker with a fixed random seed for reproducibility.

## Configuration

| Setting | Value |
|---------|-------|
| Random seed | `42` |
| Products | 500 rows |
| Customers | 10,000 rows |
| Orders | 100,000 rows |
| Output directory | `data/` (repo root) |

## Generation Order

1. **Products** — clean primary keys (`product_id` 1–500); no intentional defects.
2. **Customers** — base rows, then inject NULL emails and duplicate `customer_id` keys.
3. **Orders** — base rows referencing valid parent IDs, then inject NULL FKs, orphan FKs, and duplicate `order_id` keys.

## Intentional Quality Defects

| File | Defect | Expected Count | Silver Check |
|------|--------|----------------|--------------|
| customers.csv | NULL `email` | 50 | Completeness |
| customers.csv | Duplicate `customer_id` keys | 10 | Uniqueness |
| orders.csv | NULL `customer_id` | 100 | Completeness |
| orders.csv | NULL `product_id` | 200 | Completeness |
| orders.csv | Orphan `customer_id` | 50 | Referential Integrity |
| orders.csv | Orphan `product_id` | 30 | Referential Integrity |
| orders.csv | Duplicate `order_id` keys | 20 | Uniqueness |
| products.csv | — | 0 | — |

### Duplicate key interpretation

For uniqueness defects, **10 customer_id keys** and **20 order_id keys** each appear on **two rows** (the generator reassigns one row per key to match another row’s ID). That yields 20 and 40 rows participating in duplicate groups respectively.

### Orphan FK values

Orphan foreign keys use IDs starting at `900001`, outside valid parent ranges (customers 1–10000, products 1–500).

### Defect overlap

NULL FK injections and orphan FK injections use **disjoint row sets** so each defect type is independently countable.

## Total Problematic Rows

Assignment cites ~700 problematic rows. Exact totals depend on counting method:

| Counting method | Approximate total |
|-----------------|-------------------|
| Defect markers only (sum of counts above) | 460 |
| Rows affected by duplicate keys (×2 per key) | 500 |
| All rows failing any single check (with overlap) | lower than sum |

The generator validates **exact counts per defect type**, not a single ambiguous total.

## Self-Validation

After writing CSVs, `generate_sample_data.py` runs `validation.py` and prints PASS/FAIL for each expected defect count. Exit code `0` means all checks passed; `1` means regeneration or logic fix is required.

## Dependencies

- `pandas`
- `faker`

Install with: `pip install pandas faker`
