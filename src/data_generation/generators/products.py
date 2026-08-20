"""Product sample data generation."""

from __future__ import annotations

import random

import pandas as pd
from faker import Faker

from config import PRODUCT_CATEGORIES, PRODUCT_COUNT
from utils import decimal_str


def generate_products(fake: Faker, rng: random.Random) -> pd.DataFrame:
    """Generate a clean products DataFrame with no intentional defects."""
    rows = []
    for product_id in range(1, PRODUCT_COUNT + 1):
        price = round(rng.uniform(5.0, 500.0), 2)
        cost = round(price * rng.uniform(0.3, 0.7), 2)
        rows.append(
            {
                "product_id": product_id,
                "product_name": fake.catch_phrase(),
                "category": rng.choice(PRODUCT_CATEGORIES),
                "price": decimal_str(price),
                "cost": decimal_str(cost),
                "stock_quantity": rng.randint(0, 500),
                "reorder_level": rng.randint(10, 100),
            }
        )

    return pd.DataFrame(rows)
