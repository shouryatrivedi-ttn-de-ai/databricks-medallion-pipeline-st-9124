"""Order sample data generation and defect injection."""

from __future__ import annotations

import random
from datetime import date, timedelta

import pandas as pd
from faker import Faker

from config import (
    DUPLICATE_ORDER_ID_KEYS,
    NULL_CUSTOMER_ID_COUNT,
    NULL_PRODUCT_ID_COUNT,
    ORDER_COUNT,
    ORDER_STATUSES,
    ORPHAN_CUSTOMER_ID_COUNT,
    ORPHAN_CUSTOMER_ID_START,
    ORPHAN_PRODUCT_ID_COUNT,
    ORPHAN_PRODUCT_ID_START,
)
from utils import decimal_str, random_date_between


def generate_orders(
    fake: Faker,
    rng: random.Random,
    customers_df: pd.DataFrame,
    products_df: pd.DataFrame,
) -> pd.DataFrame:
    """Generate base order rows, then inject intentional quality defects."""
    df = _generate_base_orders(fake, rng, customers_df, products_df)
    return _inject_defects(df, rng)


def _generate_base_orders(
    fake: Faker,
    rng: random.Random,
    customers_df: pd.DataFrame,
    products_df: pd.DataFrame,
) -> pd.DataFrame:
    valid_customer_ids = customers_df["customer_id"].unique().tolist()
    valid_product_ids = products_df["product_id"].tolist()

    order_start = date(2023, 1, 1)
    order_end = date(2024, 12, 31)

    rows = []
    for order_id in range(1, ORDER_COUNT + 1):
        customer_id = rng.choice(valid_customer_ids)
        product_id = rng.choice(valid_product_ids)
        quantity = rng.randint(1, 10)
        unit_price = round(rng.uniform(5.0, 500.0), 2)
        total_amount = round(quantity * unit_price, 2)
        order_status = rng.choice(ORDER_STATUSES)
        order_date = random_date_between(rng, order_start, order_end)

        payment_date = None
        if order_status == "Completed":
            payment_offset = rng.randint(0, 14)
            payment_date = (order_date + timedelta(days=payment_offset)).isoformat()

        rows.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "order_date": order_date.isoformat(),
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": decimal_str(unit_price),
                "total_amount": decimal_str(total_amount),
                "order_status": order_status,
                "payment_date": payment_date,
            }
        )

    return pd.DataFrame(rows)


def _inject_defects(df: pd.DataFrame, rng: random.Random) -> pd.DataFrame:
    df = df.copy()
    all_indices = list(range(len(df)))

    # Completeness: NULL customer_id and product_id on disjoint row sets
    null_customer_indices = rng.sample(all_indices, NULL_CUSTOMER_ID_COUNT)
    remaining = [i for i in all_indices if i not in null_customer_indices]
    null_product_indices = rng.sample(remaining, NULL_PRODUCT_ID_COUNT)

    df.loc[null_customer_indices, "customer_id"] = None
    df.loc[null_product_indices, "product_id"] = None

    # Referential integrity: orphan FKs on rows that still have non-null FKs
    ri_customer_pool = [
        i
        for i in all_indices
        if i not in null_customer_indices and pd.notna(df.at[i, "customer_id"])
    ]
    ri_product_pool = [
        i
        for i in all_indices
        if i not in null_product_indices and pd.notna(df.at[i, "product_id"])
    ]

    orphan_customer_indices = rng.sample(ri_customer_pool, ORPHAN_CUSTOMER_ID_COUNT)
    orphan_product_indices = rng.sample(ri_product_pool, ORPHAN_PRODUCT_ID_COUNT)

    for offset, idx in enumerate(orphan_customer_indices):
        df.at[idx, "customer_id"] = ORPHAN_CUSTOMER_ID_START + offset

    for offset, idx in enumerate(orphan_product_indices):
        df.at[idx, "product_id"] = ORPHAN_PRODUCT_ID_START + offset

    # Uniqueness: 20 order_id keys appear twice (40 rows involved)
    duplicate_row_indices = rng.sample(all_indices, DUPLICATE_ORDER_ID_KEYS * 2)
    source_indices = duplicate_row_indices[:DUPLICATE_ORDER_ID_KEYS]
    target_indices = duplicate_row_indices[DUPLICATE_ORDER_ID_KEYS:]
    for source_idx, target_idx in zip(source_indices, target_indices, strict=True):
        df.at[target_idx, "order_id"] = df.at[source_idx, "order_id"]

    return df
