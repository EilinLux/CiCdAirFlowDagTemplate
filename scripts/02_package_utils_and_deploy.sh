#!/usr/bin/env bash
# ==============================================================================
# Step 02: Package Shared PySpark `utils.zip` & Deploy DAGs to Cloud Composer
# ==============================================================================
# Usage:
#   ./scripts/02_package_utils_and_deploy.sh
#
# What this script does:
#   1. Loads `_DAGS_DIRECTORY` and `_DAGS_BUCKET` from `.env`.
#   2. Packages `dags/spark_transformations_r2_es_dev/utils/*.py` into
#      `dags/spark_transformations_r2_es_dev/utils.zip` so Dataproc workers
#      receive the latest version of `some_utility_function()` and
#      `calculate_net_revenue()`.
#   3. Executes `utils/add_dags_to_composer.py` to upload all production DAGs
#      and nested PySpark artifacts (`*_job.py`, `utils.zip`) to the target
#      Cloud Composer GCS bucket (`gs://${_DAGS_BUCKET}/dags/`).
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "${REPO_ROOT}/.env"
    set +a
else
    echo "Error: .env file not found. Run 'cp .env.example .env' and configure _DAGS_BUCKET."
    exit 1
fi

echo "=================================================================="
echo "[1/2] Packaging shared PySpark helpers into utils.zip..."
echo "=================================================================="
python3 - <<'PYEOF'
import pathlib
import zipfile

base = pathlib.Path("dags/spark_transformations_r2_es_dev")
zip_path = base / "utils.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for py_file in sorted((base / "utils").rglob("*.py")):
        zf.write(py_file, py_file.relative_to(base))
print(f"Successfully packaged {zip_path}")
PYEOF

echo "=================================================================="
echo "[2/2] Synchronizing DAGs & utils.zip to gs://${_DAGS_BUCKET}/dags/..."
echo "=================================================================="
uv run python utils/add_dags_to_composer.py \
    --dags_directory="${_DAGS_DIRECTORY:-dags}" \
    --dags_bucket="${_DAGS_BUCKET}"
