"""
Generate sample CSV files for the Databricks medallion pipeline assignment.

Outputs:
  data/customers.csv  (~10,000 rows)
  data/orders.csv     (~100,000 rows)
  data/products.csv   (~500 rows)

Includes intentional data-quality defects and self-validates counts after generation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# Allow imports from this package directory when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import CUSTOMER_COUNT, DATA_DIR, ORDER_COUNT, PRODUCT_COUNT, RANDOM_SEED
from generators.customers import generate_customers
from generators.orders import generate_orders
from generators.products import generate_products
from utils import create_faker, create_rng
from validation import print_validation_report, validate_all

INTEGER_CSV_COLUMNS = frozenset(
    {
        "customer_id",
        "order_id",
        "product_id",
        "quantity",
        "stock_quantity",
        "reorder_level",
    }
)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    """Write CSV with nullable integer columns formatted as integers, not floats."""
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    for column in out.columns:
        if column in INTEGER_CSV_COLUMNS:
            out[column] = pd.to_numeric(out[column], errors="coerce").astype("Int64")
    out.to_csv(path, index=False, na_rep="")


def main() -> int:
    print(f"Generating sample data (seed={RANDOM_SEED})...")
    fake = create_faker()
    rng = create_rng()

    products_df = generate_products(fake, rng)
    customers_df = generate_customers(fake, rng)
    orders_df = generate_orders(fake, rng, customers_df, products_df)

    print(f"  products:  {len(products_df):,} rows")
    print(f"  customers: {len(customers_df):,} rows")
    print(f"  orders:    {len(orders_df):,} rows")

    write_csv(products_df, DATA_DIR / "products.csv")
    write_csv(customers_df, DATA_DIR / "customers.csv")
    write_csv(orders_df, DATA_DIR / "orders.csv")

    print(f"\nWritten CSVs to: {DATA_DIR}")

    results = validate_all(customers_df, orders_df, products_df)
    all_passed = print_validation_report(results)

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
