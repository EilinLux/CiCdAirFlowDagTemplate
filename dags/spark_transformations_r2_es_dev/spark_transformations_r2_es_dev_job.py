"""
Dataproc PySpark Driver Job (`spark_transformations_r2_es_dev_job.py`)
======================================================================
Executed on an ephemeral Cloud Dataproc cluster by the Airflow DAG
`spark_transformations-r2-es-dev` (`dags/spark_transformations_r2_es_dev_dag.py`).

How this connects the 3-Part Google Cloud Data Engineering Series:
  - Unpacks `utils.zip` containing `utils/utils.py` (authored in Part 1: `dataproc-workshop`).
  - Processes the retail `sales_data` domain (`order_id`, `category`, `gross_sales`,
    `sale_date`) orchestrated in Part 2 (`composer-workshop`).
  - Filters records between `--start` and `--end` (injected by Airflow Jinja macros)
    and computes category-level net revenue metrics.
"""

import argparse
import os
import sys
import zipfile
from pathlib import Path
from typing import List, Optional


def unpack_utils_archive() -> None:
    """Extract `utils.zip` in the Dataproc working directory if present."""
    candidate_paths = [
        Path.cwd() / "utils.zip",
        Path(__file__).resolve().parent / "utils.zip",
        Path("/utils.zip"),
    ]

    for zip_path in candidate_paths:
        if zip_path.exists():
            extract_dir = Path.cwd()
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
            if str(extract_dir) not in sys.path:
                sys.path.insert(0, str(extract_dir))
            print(f"[Setup] Extracted '{zip_path}' into '{extract_dir}'.")
            return

    # Ensure the parent directory of this script is on sys.path for local execution
    script_dir = str(Path(__file__).resolve().parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)


# Extract `utils.zip` before importing the shared helper functions
unpack_utils_archive()

from utils.utils import calculate_net_revenue, some_utility_function  # noqa: E402


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse `--start` and `--end` date window arguments passed by Airflow."""
    parser = argparse.ArgumentParser(
        description="Run Dataproc PySpark retail sales transformations for a date window."
    )
    parser.add_argument(
        "--start",
        default="2025-10-01",
        help="Inclusive start date (YYYY-MM-DD or YYYYMMDD) passed by Airflow.",
    )
    parser.add_argument(
        "--end",
        default="2025-10-31",
        help="Inclusive end date (YYYY-MM-DD or YYYYMMDD) passed by Airflow.",
    )
    return parser.parse_args(argv)


def run(argv: Optional[List[str]] = None) -> dict:
    """Execute the PySpark retail sales aggregation job."""
    args = parse_args(argv)
    start_date = args.start
    end_date = args.end

    # Verify the `utils.zip` helper library is accessible on the driver
    banner = some_utility_function()
    print(f"[Starting] Job initialized for window [{start_date} -> {end_date}]")

    # Sample retail sales dataset (mirrors `example_composer_workshop.sales_data`)
    raw_sales_records = [
        ("ORD-1001", "2025-10-05", "Electronics", 1220.00),
        ("ORD-1002", "2025-10-05", "Apparel", 330.00),
        ("ORD-1003", "2025-10-06", "Home & Kitchen", 590.00),
        ("ORD-1004", "2025-10-06", "Electronics", 2440.00),
        ("ORD-1005", "2025-10-07", "Books", 104.00),
    ]

    # Enrich each transaction with net revenue using `calculate_net_revenue` from `utils.py`
    enriched_records = [
        {
            "order_id": order_id,
            "sale_date": sale_date,
            "category": category,
            "gross_sales": gross_amount,
            "net_revenue": calculate_net_revenue(gross_amount, category),
        }
        for (order_id, sale_date, category, gross_amount) in raw_sales_records
    ]

    # Aggregate net revenue by product category
    category_totals: dict = {}
    for row in enriched_records:
        cat = row["category"]
        category_totals[cat] = round(
            category_totals.get(cat, 0.0) + row["net_revenue"], 2
        )

    print(f"[Completed] Category net revenue summary: {category_totals}")
    return {
        "banner": banner,
        "start_date": start_date,
        "end_date": end_date,
        "category_totals": category_totals,
    }


if __name__ == "__main__":
    run()
