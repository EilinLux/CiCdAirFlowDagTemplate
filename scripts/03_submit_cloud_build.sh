#!/usr/bin/env bash
# ==============================================================================
# Step 03: Trigger Google Cloud Build CI (Test) & CD (Deploy) Pipelines
# ==============================================================================
# Usage:
#   ./scripts/03_submit_cloud_build.sh [ci|cd|both]
#
# What this script does:
#   1. Loads `_PROJECT_ID`, `_REGION`, `_DAGS_DIRECTORY`, `_DAGS_BUCKET`, and
#      `_WORKER_POOL` from `.env`.
#   2. Submits `test-dags.cloudbuild.yaml` (Continuous Integration) and/or
#      `add-dags-to-composer.cloudbuild.yaml` (Continuous Delivery) to
#      Google Cloud Build with the configured substitutions.
# ==============================================================================
set -euo pipefail

MODE="${1:-both}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ -f "${REPO_ROOT}/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "${REPO_ROOT}/.env"
    set +a
else
    echo "Error: .env file not found. Run 'cp .env.example .env' first."
    exit 1
fi

SUBSTITUTIONS="_PROJECT_ID=${_PROJECT_ID},_REGION=${_REGION},_DAGS_DIRECTORY=${_DAGS_DIRECTORY:-dags},_DAGS_BUCKET=${_DAGS_BUCKET},_WORKER_POOL=${_WORKER_POOL}"

if [[ "${MODE}" == "ci" || "${MODE}" == "both" ]]; then
    echo "=================================================================="
    echo "[CI] Submitting test-dags.cloudbuild.yaml to Cloud Build..."
    echo "=================================================================="
    gcloud builds submit . \
        --project="${_PROJECT_ID}" \
        --config="test-dags.cloudbuild.yaml" \
        --substitutions="${SUBSTITUTIONS}"
fi

if [[ "${MODE}" == "cd" || "${MODE}" == "both" ]]; then
    echo "=================================================================="
    echo "[CD] Submitting add-dags-to-composer.cloudbuild.yaml to Cloud Build..."
    echo "=================================================================="
    gcloud builds submit . \
        --project="${_PROJECT_ID}" \
        --config="add-dags-to-composer.cloudbuild.yaml" \
        --substitutions="${SUBSTITUTIONS}"
fi
