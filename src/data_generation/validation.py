"""Post-generation validation of intentional data-quality defects."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from config import (
    DUPLICATE_CUSTOMER_ID_KEYS,
    DUPLICATE_ORDER_ID_KEYS,
    NULL_CUSTOMER_ID_COUNT,
    NULL_EMAIL_COUNT,
    NULL_PRODUCT_ID_COUNT,
    ORPHAN_CUSTOMER_ID_COUNT,
    ORPHAN_PRODUCT_ID_COUNT,
)


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of a single defect count check."""

    name: str
    expected: int
    actual: int

    @property
    def passed(self) -> bool:
        return self.actual == self.expected


def _is_null(series: pd.Series) -> pd.Series:
    return series.isna() | (series.astype(str).str.strip() == "")


def _duplicate_key_count(df: pd.DataFrame, key_col: str) -> int:
    counts = df.groupby(key_col, dropna=False).size()
    return int(counts[counts > 1].shape[0])


def validate_customers(df: pd.DataFrame) -> list[ValidationResult]:
    null_emails = int(_is_null(df["email"]).sum())
    duplicate_keys = _duplicate_key_count(df, "customer_id")

    return [
        ValidationResult("customers.null_email", NULL_EMAIL_COUNT, null_emails),
        ValidationResult(
            "customers.duplicate_customer_id_keys",
            DUPLICATE_CUSTOMER_ID_KEYS,
            duplicate_keys,
        ),
    ]


def validate_orders(
    df: pd.DataFrame,
    customers_df: pd.DataFrame,
    products_df: pd.DataFrame,
) -> list[ValidationResult]:
    valid_customer_ids = set(customers_df["customer_id"].tolist())
    valid_product_ids = set(products_df["product_id"].tolist())

    null_customer_id = int(_is_null(df["customer_id"]).sum())
    null_product_id = int(_is_null(df["product_id"]).sum())

    orphan_customer_id = int(
        (
            df["customer_id"].notna()
            & ~df["customer_id"].isin(valid_customer_ids)
        ).sum()
    )

    orphan_product_id = int(
        (
            df["product_id"].notna()
            & ~df["product_id"].isin(valid_product_ids)
        ).sum()
    )

    duplicate_order_keys = _duplicate_key_count(df, "order_id")

    return [
        ValidationResult("orders.null_customer_id", NULL_CUSTOMER_ID_COUNT, null_customer_id),
        ValidationResult("orders.null_product_id", NULL_PRODUCT_ID_COUNT, null_product_id),
        ValidationResult(
            "orders.orphan_customer_id",
            ORPHAN_CUSTOMER_ID_COUNT,
            orphan_customer_id,
        ),
        ValidationResult(
            "orders.orphan_product_id",
            ORPHAN_PRODUCT_ID_COUNT,
            orphan_product_id,
        ),
        ValidationResult(
            "orders.duplicate_order_id_keys",
            DUPLICATE_ORDER_ID_KEYS,
            duplicate_order_keys,
        ),
    ]


def validate_all(
    customers_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    products_df: pd.DataFrame,
) -> list[ValidationResult]:
    """Run all defect validations and return individual results."""
    results = validate_customers(customers_df)
    results.extend(validate_orders(orders_df, customers_df, products_df))
    return results


def print_validation_report(results: list[ValidationResult]) -> bool:
    """Print a human-readable report. Returns True if all checks passed."""
    print("\n=== Data Generation Validation ===")
    all_passed = True
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(
            f"  [{status}] {result.name}: expected={result.expected}, actual={result.actual}"
        )
        if not result.passed:
            all_passed = False

    problematic_rows = sum(r.actual for r in results)
    print(f"\n  Total defect markers counted: {problematic_rows}")
    print(f"  Overall: {'ALL CHECKS PASSED' if all_passed else 'VALIDATION FAILED'}")
    return all_passed
