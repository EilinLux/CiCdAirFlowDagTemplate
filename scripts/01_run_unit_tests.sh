#!/usr/bin/env bash
# ==============================================================================
# Step 01: Run Local Airflow DAG Integrity & GCS Sync Unit Tests (`uv` + `pytest`)
# ==============================================================================
# Usage:
#   ./scripts/01_run_unit_tests.sh
#
# What this script does:
#   1. Loads configuration variables from `.env` (or `.env.example` as fallback).
#   2. Synchronizes the Python virtual environment via `uv sync`.
#   3. Runs `uv run pytest -v dags/ utils/` to validate:
#      - Zero syntax or import errors across all DAGs (`example_dag`, `example2_dag`,
#        `spark_transformations_r2_es_dev_dag`).
#      - Zero circular task dependencies (`check_cycle`).
#      - Proper execution of the PySpark driver job (`spark_transformations_r2_es_dev_job.py`)
#        and unpacking of `utils.zip`.
#      - Proper file filtering and upload logic in `utils/add_dags_to_composer.py`.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# Load environment variables from .env (or .env.example if .env does not exist)
if [[ -f "${REPO_ROOT}/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "${REPO_ROOT}/.env"
    set +a
elif [[ -f "${REPO_ROOT}/.env.example" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "${REPO_ROOT}/.env.example"
    set +a
fi

echo "=================================================================="
echo "[1/2] Synchronizing Python dependencies with uv..."
echo "=================================================================="
uv sync

echo "=================================================================="
echo "[2/2] Running Airflow DAG & Composer CI/CD unit tests..."
echo "=================================================================="
uv run pytest -v dags/ utils/
