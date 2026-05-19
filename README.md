# Cloud Composer CI/CD DAG Deployment Template (`CiCdAirFlowDagTemplate`)

> **Google Cloud Data Engineering Series — Part 3 of 3**
> 1. [**Part 1: Cloud Dataproc & PySpark Workshop (`dataproc-workshop`)**](../dataproc-workshop) — Build distributed PySpark transformations (`process_data.py`), package shared helper modules (`utils.py`), and run Serverless Spark on BigQuery.
> 2. [**Part 2: Cloud Composer & Apache Airflow Workshop (`composer-workshop`)**](../composer-workshop) — Orchestrate daily retail sales pipelines across GCS, BigQuery, and ephemeral Dataproc clusters with Airflow 2.10.
> 3. **Part 3: Production CI/CD for Cloud Composer (`CiCdAirFlowDagTemplate` — *You are here*)** — Automate DAG integrity testing, `utils.zip` packaging, and zero-touch Cloud Build deployment to Cloud Composer.

---

## 1. Product & Architecture Overview

When moving Apache Airflow workflows from interactive workshop notebooks into enterprise production on **Google Cloud Composer**, manual `gcloud storage cp` uploads quickly become error-prone:
- A single syntax error, unquoted Jinja macro, or circular task dependency in a `.py` file can break the DAG parsing loop in Cloud Composer.
- Complex PySpark jobs require companion Python archives (`utils.zip`) and driver scripts (`*_job.py`) to be versioned and synchronized alongside the orchestrating Airflow DAG.
- Test files (`*_test.py`) and local development helpers must never pollute the production Cloud Composer GCS bucket.

This repository provides a **production-ready CI/CD template** powered by **`uv`**, **`pytest`**, and **Google Cloud Build** that solves all three challenges:
1. **Continuous Integration (`test-dags.cloudbuild.yaml`)**: Every change is validated in an isolated `uv` environment using `pytest` (`dags/internal_unit_testing.py`) to verify DAG import health, cycle-free task graphs (`check_cycle`), and PySpark driver logic.
2. **Continuous Delivery (`add-dags-to-composer.cloudbuild.yaml`)**: Once tests pass, `utils/add_dags_to_composer.py` stages only production DAGs and nested PySpark job bundles (`utils.zip`), automatically stripping out unit tests and cache files before uploading to `gs://${_DAGS_BUCKET}/dags/`.

---

## 2. The Storyline: How theRepository Connects End-to-End

```
┌────────────────────────────────────────────────────────────────────────────┐
│ 1. Local Authoring & Configuration (.env + pyproject.toml)                 │
│    • Configure GCP project, Composer bucket & Dataproc sizing in `.env`    │
│    • Author PySpark helpers in `dags/.../utils/utils.py` -> `utils.zip`    │
└───────────────────────────────────────┬────────────────────────────────────┘
                                        ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ 2. Continuous Integration (scripts/01_run_unit_tests.sh & Cloud Build CI)  │
│    • `dags/example_dag_test.py` & `dags/example2_dag_test.py`              │
│    • `dags/spark_transformations_r2_es_dev_dag_test.py` validates the      │
│      ephemeral Dataproc lifecycle (`create >> run_pyspark >> delete`)      │
│    • `utils/add_dags_to_composer_test.py` verifies GCS sync filtering      │
└───────────────────────────────────────┬────────────────────────────────────┘
                                        ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ 3. Continuous Delivery (scripts/02_package_utils_and_deploy.sh & CD YAML)  │
│    • `utils/add_dags_to_composer.py` filters out `*_test.py` & helpers     │
│    • Uploads top-level DAGs (`*.py`) and nested `utils.zip` + `*_job.py`   │
│      directly to `gs://${_DAGS_BUCKET}/dags/`                              │
└───────────────────────────────────────┬────────────────────────────────────┘
                                        ▼
┌────────────────────────────────────────────────────────────────────────────┐
│ 4. Production Execution in Cloud Composer (`spark_transformations-r2-es-dev`)│
│    • Provisions an internal-IP Dataproc cluster with Component Gateway     │
│    • Runs `spark_transformations_r2_es_dev_job.py` with `--start`/`--end`  │
│    • Unpacks `utils.zip` (`some_utility_function`, `calculate_net_revenue`)│
│    • Tears down the cluster with `TriggerRule.ALL_DONE`                    │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Repository Structure

```text
CiCdAirFlowDagTemplate/
├── .env.example                                   # Documented environment variable template
├── .gitignore                                     # Excludes .venv/, .env, caches, and Airflow DBs
├── pyproject.toml                                 # Modern `uv` project & pytest configuration
├── test-dags.cloudbuild.yaml                      # Cloud Build CI pipeline (uv sync + pytest)
├── add-dags-to-composer.cloudbuild.yaml           # Cloud Build CD pipeline (GCS DAG & zip sync)
├── dags/
│   ├── internal_unit_testing.py                   # Shared DAG cycle & import assertion helper
│   ├── example_dag.py                             # Baseline smoke-test DAG (`composer_sample_dag`)
│   ├── example_dag_test.py                        # Unit test for `example_dag.py`
│   ├── example2_dag.py                            # Secondary smoke-test DAG (`composer_sample_dag_2`)
│   ├── example2_dag_test.py                       # Unit test for `example2_dag.py`
│   ├── spark_transformations_r2_es_dev_dag.py     # Ephemeral Dataproc + PySpark ETL DAG
│   ├── spark_transformations_r2_es_dev_dag_test.py# Unit test for Dataproc DAG & PySpark driver
│   └── spark_transformations_r2_es_dev/
│       ├── spark_transformations_r2_es_dev_job.py # PySpark retail sales driver script
│       ├── utils.zip                              # Packaged utility archive distributed via `--py-files`
│       └── utils/
│           ├── __init__.py
│           └── utils.py                           # Shared `some_utility_function` & `calculate_net_revenue`
├── utils/
│   ├── add_dags_to_composer.py                    # GCS synchronization script for DAGs & nested zip folders
│   └── add_dags_to_composer_test.py               # Unit tests for staging & GCS upload functions
└── scripts/
    ├── 01_run_unit_tests.sh                       # Run the complete local pytest suite via `uv`
    ├── 02_package_utils_and_deploy.sh             # Rebuild `utils.zip` and sync to Composer GCS bucket
    └── 03_submit_cloud_build.sh                   # Trigger Cloud Build CI and CD pipelines
```

---

## 4. Quickstart & Usage

### Prerequisites
- **[`uv`](https://docs.astral.sh/uv/)** installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Google Cloud SDK (`gcloud`)** authenticated (`gcloud auth login` & `gcloud auth application-default login`)

### Step 1: Configure `.env`
Copy the example configuration file and adjust for your Google Cloud project:
```bash
cp .env.example .env
```

### Step 2: Run Unit & DAG Integrity Tests Locally
Validate all Airflow DAGs, PySpark jobs, and GCS deployment utilities:
```bash
./scripts/01_run_unit_tests.sh
# Or directly via uv:
uv run pytest -v dags/ utils/
```

### Step 3: Package `utils.zip` & Deploy Manually to Cloud Composer
```bash
./scripts/02_package_utils_and_deploy.sh
```

### Step 4: Run Automated CI/CD with Google Cloud Build
Submit the Continuous Integration (`test-dags.cloudbuild.yaml`) or Continuous Delivery (`add-dags-to-composer.cloudbuild.yaml`) pipelines:
```bash
# Run both CI and CD pipelines in Cloud Build
./scripts/03_submit_cloud_build.sh both

# Or run only CI (unit tests)
./scripts/03_submit_cloud_build.sh ci
```

---

## 5. Environment Variables Reference (`.env`)

| Category | Variable | Description | Default / Example |
| :--- | :--- | :--- | :--- |
| **GCP & Composer** | `_PROJECT_ID` | Google Cloud Project ID | `gai-community29oct-7500` |
| **GCP & Composer** | `_REGION` / `_ZONE` | Region and zone for Composer & Dataproc | `europe-west1` / `europe-west1-b` |
| **GCP & Composer** | `_DAGS_DIRECTORY` | Local directory containing DAGs | `dags` |
| **GCP & Composer** | `_DAGS_BUCKET` | Target Cloud Composer GCS bucket (no `gs://`) | `gai-community29oct-7500-composer-dags` |
| **GCP & Composer** | `_WORKER_POOL` | Cloud Build private worker pool name | `composer-cicd-worker-pool` |
| **GCP & Composer** | `_SUBNETWORK` | Subnetwork URI for internal-IP Dataproc VMs | `projects/.../subnetworks/default` |
| **GCP & Composer** | `_SERVICE_ACCOUNT` | Composer / Dataproc worker service account | `composer-worker-sa@...` |
| **Dataproc Sizing** | `_IMAGE` | Dataproc image version | `2.2-debian12` |
| **Dataproc Sizing** | `_MASTER_MACHINE` / `_WORKER_MACHINE` | Compute Engine machine types | `n2-standard-4` |
| **Dataproc Sizing** | `_MASTER_DISK_SIZE` / `_WORKER_DISK_SIZE` | Boot disk sizes in GB | `100` / `200` |
| **Dataproc Sizing** | `_WORKER_NUMBER` / `_WORKER_PREEMPTIBLE_NUMBER` | Primary & Spot worker counts | `2` / `0` |
| **Dataproc Sizing** | `_MAX_IDLE` | Idle TTL in seconds before auto-deletion | `1800` |
| **Dataproc Sizing** | `_TAGS` | Space-separated firewall network tags | `allow-internal-dataproc-dev ...` |
| **DAG & Release** | `_SCHEDULER` | Cron schedule or Airflow preset | `@daily` |
| **DAG & Release** | `_GOAL` / `_RELEASE` / `_LOCAL_MARKET` / `_ENV` | Naming tokens (`<goal>-<release>-<lm>-<env>`) | `spark_transformations` / `r2` / `es` / `dev` |
| **DAG & Release** | `_SPARK_JAR` | Spark BigQuery Connector JAR URI | `gs://spark-lib/bigquery/...` |
