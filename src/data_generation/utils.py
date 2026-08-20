"""Shared helpers for sample data generation."""

from __future__ import annotations

import random
from datetime import date, timedelta

from faker import Faker

from config import RANDOM_SEED


def create_faker() -> Faker:
    """Return a seeded Faker instance for deterministic generation."""
    fake = Faker()
    Faker.seed(RANDOM_SEED)
    fake.seed_instance(RANDOM_SEED)
    return fake


def create_rng() -> random.Random:
    """Return a seeded random.Random for index selection."""
    return random.Random(RANDOM_SEED)


def random_date_between(
    rng: random.Random,
    start: date,
    end: date,
) -> date:
    """Pick a random date in [start, end] inclusive."""
    days = (end - start).days
    return start + timedelta(days=rng.randint(0, days))


def decimal_str(value: float) -> str:
    """Format a float as a two-decimal string for CSV output."""
    return f"{value:.2f}"
