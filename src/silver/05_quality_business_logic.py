"""
Optional business-rule validation (stretch).

Not implemented in the current Silver release.
"""

from __future__ import annotations

from pyspark.sql import DataFrame

from silver.silver_utils import CheckMetric


def apply_business_logic_checks(entity: str, df: DataFrame) -> tuple[DataFrame, list[CheckMetric]]:
    return df, []
