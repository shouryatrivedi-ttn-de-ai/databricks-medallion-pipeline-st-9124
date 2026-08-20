"""Configuration constants for sample data generation."""

from pathlib import Path

# Reproducibility
RANDOM_SEED = 42

# Row volumes (assignment targets)
PRODUCT_COUNT = 500
CUSTOMER_COUNT = 10000
ORDER_COUNT = 100000

# Intentional defect counts (assignment specification)
NULL_EMAIL_COUNT = 50
DUPLICATE_CUSTOMER_ID_KEYS = 10

NULL_CUSTOMER_ID_COUNT = 100
NULL_PRODUCT_ID_COUNT = 200
ORPHAN_CUSTOMER_ID_COUNT = 50
ORPHAN_PRODUCT_ID_COUNT = 30
DUPLICATE_ORDER_ID_KEYS = 20

# Orphan FK values — outside valid parent ID ranges
ORPHAN_CUSTOMER_ID_START = 900001
ORPHAN_PRODUCT_ID_START = 900001

# Output paths (repo root / data /)
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"

CUSTOMER_SEGMENTS = ("Premium", "Standard", "Basic")
ORDER_STATUSES = ("Pending", "Completed", "Cancelled")
PRODUCT_CATEGORIES = (
    "Electronics",
    "Clothing",
    "Home",
    "Sports",
    "Books",
    "Beauty",
    "Toys",
    "Automotive",
)
