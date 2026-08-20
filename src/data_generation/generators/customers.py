"""Customer sample data generation and defect injection."""

from __future__ import annotations

import random
from datetime import date

import pandas as pd
from faker import Faker

from config import (
    CUSTOMER_COUNT,
    CUSTOMER_SEGMENTS,
    DUPLICATE_CUSTOMER_ID_KEYS,
    NULL_EMAIL_COUNT,
)
from utils import decimal_str, random_date_between


def generate_customers(fake: Faker, rng: random.Random) -> pd.DataFrame:
    """Generate base customer rows, then inject intentional quality defects."""
    df = _generate_base_customers(fake, rng)
    return _inject_defects(df, rng)


def _generate_base_customers(fake: Faker, rng: random.Random) -> pd.DataFrame:
    rows = []
    signup_start = date(2018, 1, 1)
    signup_end = date(2024, 12, 31)

    for customer_id in range(1, CUSTOMER_COUNT + 1):
        rows.append(
            {
                "customer_id": customer_id,
                "customer_name": fake.name(),
                "email": fake.email(),
                "country": fake.country(),
                "signup_date": random_date_between(rng, signup_start, signup_end).isoformat(),
                "customer_segment": rng.choice(CUSTOMER_SEGMENTS),
                "lifetime_value": decimal_str(round(rng.uniform(100.0, 50000.0), 2)),
            }
        )

    return pd.DataFrame(rows)


def _inject_defects(df: pd.DataFrame, rng: random.Random) -> pd.DataFrame:
    df = df.copy()

    # Completeness: NULL email on 50 rows
    null_email_indices = rng.sample(range(len(df)), NULL_EMAIL_COUNT)
    df.loc[null_email_indices, "email"] = None

    # Uniqueness: 10 customer_id keys appear twice (20 rows involved)
    duplicate_row_indices = rng.sample(range(len(df)), DUPLICATE_CUSTOMER_ID_KEYS * 2)
    source_indices = duplicate_row_indices[:DUPLICATE_CUSTOMER_ID_KEYS]
    target_indices = duplicate_row_indices[DUPLICATE_CUSTOMER_ID_KEYS:]
    for source_idx, target_idx in zip(source_indices, target_indices, strict=True):
        df.at[target_idx, "customer_id"] = df.at[source_idx, "customer_id"]

    return df
