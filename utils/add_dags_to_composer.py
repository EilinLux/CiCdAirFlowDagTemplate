# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Cloud Composer CI/CD Synchronization Utility (`utils/add_dags_to_composer.py`)
==============================================================================
Synchronizes validated Airflow DAG files (`dags/*.py`) and nested PySpark job
artifacts (`dags/<job_folder>/*_job.py`, `utils.zip`) to a Cloud Composer
environment's Cloud Storage bucket (`gs://<dags_bucket>/dags/`).

Key Features:
  - Automatically filters out unit tests (`*_test.py`), test helpers
    (`internal_unit_testing.py`), `__init__.py`, and `__pycache__` directories
    so only production DAGs and job artifacts reach Cloud Composer.
  - Supports `.env` defaults (`_DAGS_DIRECTORY`, `_DAGS_BUCKET`) as well as
    explicit CLI flags (`--dags_directory`, `--dags_bucket`).
"""

# [START composer_cicd_add_dags_to_composer_utility]
import argparse
import glob
import os
from pathlib import Path
from shutil import copytree, ignore_patterns
import tempfile
from typing import List, Tuple

from dotenv import load_dotenv
from google.cloud import storage

# Load `.env` configuration if available
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Patterns excluded from Cloud Composer GCS deployment
IGNORED_PATTERNS = (
    "__init__.py",
    "*_test.py",
    "test_*.py",
    "internal_unit_testing.py",
    "__pycache__",
    "*.pyc",
)


def _create_dags_list(dags_directory: str) -> Tuple[str, List[str]]:
    """Copy `dags_directory` to a clean staging directory and return top-level DAG `.py` files."""
    if not os.path.exists(dags_directory):
        raise FileNotFoundError(
            f"DAGs directory '{dags_directory}' does not exist."
        )

    temp_dir = tempfile.mkdtemp()
    files_to_ignore = ignore_patterns(*IGNORED_PATTERNS)

    # Copy all non-ignored files into the staging directory
    copytree(dags_directory, f"{temp_dir}/", ignore=files_to_ignore, dirs_exist_ok=True)

    # Collect only top-level Python DAG files
    dags = sorted(glob.glob(f"{temp_dir}/*.py"))
    return (temp_dir, dags)


def _create_zip_folder_list(dags_directory: str) -> Tuple[str, List[str]]:
    """Copy `dags_directory` to a staging directory and return nested job/zip files."""
    if not os.path.exists(dags_directory):
        raise FileNotFoundError(
            f"DAGs directory '{dags_directory}' does not exist."
        )

    temp_dir = tempfile.mkdtemp()
    files_to_ignore = ignore_patterns(*IGNORED_PATTERNS)

    copytree(dags_directory, f"{temp_dir}/", ignore=files_to_ignore, dirs_exist_ok=True)

    # Collect files inside subdirectories (e.g., spark_transformations_r2_es_dev/*.py and utils.zip)
    nested_candidates = glob.glob(f"{temp_dir}/**/*", recursive=True)
    nested_files = sorted(
        path
        for path in nested_candidates
        if os.path.isfile(path) and os.path.dirname(path) != temp_dir
    )
    return (temp_dir, nested_files)


def upload_zip_folders_to_composer(dags_directory: str, bucket_name: str) -> None:
    """Upload nested PySpark driver scripts and `utils.zip` bundles to `gs://<bucket>/dags/`."""
    temp_dir, nested_files = _create_zip_folder_list(dags_directory)

    if len(nested_files) > 0:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        for local_path in nested_files:
            rel_path = os.path.relpath(local_path, temp_dir).replace("\\", "/")
            gcs_destination = f"dags/{rel_path}"

            blob = bucket.blob(gcs_destination)
            if local_path.endswith(".zip"):
                blob.upload_from_filename(local_path, content_type="application/zip")
            else:
                blob.upload_from_filename(local_path)
            print(f"Folder artifact {gcs_destination} uploaded to {bucket_name}/{gcs_destination}.")
    else:
        print("No nested job artifacts or zip folders to upload.")


def upload_dags_to_composer(dags_directory: str, bucket_name: str) -> None:
    """Upload top-level Airflow DAG `.py` files to `gs://<bucket>/dags/`."""
    temp_dir, dags = _create_dags_list(dags_directory)

    if len(dags) > 0:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        for local_dag_path in dags:
            rel_path = os.path.relpath(local_dag_path, temp_dir).replace("\\", "/")
            gcs_destination = f"dags/{rel_path}"

            blob = bucket.blob(gcs_destination)
            blob.upload_from_filename(local_dag_path)
            print(f"File {gcs_destination} uploaded to {bucket_name}/{gcs_destination}.")
    else:
        print("No DAGs to upload.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--dags_directory",
        default=os.environ.get("_DAGS_DIRECTORY", "dags"),
        help="Relative path to the source directory containing your DAGs (default: dags)",
    )
    parser.add_argument(
        "--dags_bucket",
        default=os.environ.get("_DAGS_BUCKET"),
        help="Name of the DAGs bucket of your Composer environment without the gs:// prefix",
    )

    args = parser.parse_args()
    if not args.dags_bucket:
        raise ValueError(
            "Missing --dags_bucket (or _DAGS_BUCKET in .env). Please specify the target Composer bucket."
        )

    upload_dags_to_composer(args.dags_directory, args.dags_bucket)
    upload_zip_folders_to_composer(args.dags_directory, args.dags_bucket)
# [END composer_cicd_add_dags_to_composer_utility]
