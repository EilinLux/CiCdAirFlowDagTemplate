"""
Shared PySpark Utility Module (`utils/utils.py` packaged inside `utils.zip`)
============================================================================
This module originates in Part 1 (`dataproc-workshop/03_submit_pyspark_jobs/scripts/utils.py`)
and is packaged into `dags/spark_transformations_r2_es_dev/utils.zip` for automated
CI/CD distribution to Cloud Composer and Cloud Dataproc worker nodes.
"""

from typing import Dict


# Standardized tax rates by retail product category
CATEGORY_TAX_RATES: Dict[str, float] = {
    "Electronics": 0.22,
    "Apparel": 0.10,
    "Home & Kitchen": 0.18,
    "Books": 0.04,
}


def some_utility_function() -> str:
    """Return a diagnostic banner confirming `utils.zip` was unpacked on the cluster."""
    message = (
        "Hello from some_utility_function in utils.py! "
        "(Unpacked from utils.zip via Cloud Composer CI/CD)"
    )
    print(message)
    return message


def get_tax_rate(category: str) -> float:
    """Return the applicable VAT/sales tax rate for a retail product category."""
    return CATEGORY_TAX_RATES.get(category, 0.20)


def calculate_net_revenue(gross_amount: float, category: str) -> float:
    """Compute net revenue after deducting category-specific tax from gross sales."""
    tax_rate = get_tax_rate(category)
    return round(gross_amount / (1.0 + tax_rate), 2)
