"""
Ephemeral Dataproc PySpark Transformation DAG (`spark_transformations-r2-es-dev`)
=================================================================================
Author: Eilin Lux (eilinlux@gmail.com)

Part 3 of the Google Cloud Data Engineering Series:
  1. `dataproc-workshop`        — Authoring the PySpark Retail Sales ETL & `utils.py`
  2. `composer-workshop`        — Orchestrating Airflow DAGs & BigQuery pipelines
  3. `CiCdAirFlowDagTemplate`   — Automating CI/CD testing & Cloud Composer deployment

Workflow Overview:
  1. `create_cluster_*`: Provisions an ephemeral, internal-IP Cloud Dataproc cluster
     with Component Gateway enabled (`enableHttpPortAccess: True`), custom labels,
     and the Spark BigQuery connector JAR pre-configured.
  2. `run_pyspark_job_*`: Submits `spark_transformations_r2_es_dev_job.py` along with
     the packaged `utils.zip` library (`pyFiles`) and execution date window arguments
     (`--start {{ prev_ds }} --end {{ ds }}`).
  3. `delete_cluster_*`: Tears down the ephemeral cluster with `TriggerRule.ALL_DONE`
     so compute resources never leak even if the Spark job fails.
"""

import datetime
import os
from pathlib import Path
from typing import List

from airflow import models
from airflow.providers.google.cloud.operators.dataproc import (
    DataprocCreateClusterOperator,
    DataprocDeleteClusterOperator,
    DataprocSubmitJobOperator,
)
from airflow.utils.trigger_rule import TriggerRule
from dotenv import load_dotenv

# Load local `.env` file if present (used during local `uv run pytest` runs)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def convert_string_to_list(raw_value: str) -> List[str]:
    """Split a space-delimited string of network tags into a clean Python list."""
    if not raw_value:
        return []
    return [tag.strip() for tag in raw_value.split(" ") if tag.strip()]


# ==============================================================================
# 1. Execution Window & Date Macros
# ==============================================================================
# Airflow Jinja macros evaluated at task runtime (YYYY-MM-DD)
start = "{{ prev_ds }}"
end = "{{ ds }}"

# Static reference date components used for cluster naming & metadata defaults
reference_date = datetime.date(2025, 10, 1)
year = "{{ execution_date.strftime('%Y') }}"
month = "{{ execution_date.strftime('%m') }}"
day = "{{ execution_date.strftime('%d') }}"

# ==============================================================================
# 2. Dataproc Cluster & Environment Configuration (from `.env` / Environment)
# ==============================================================================
storage_bucket = os.environ.get(
    "_DAGS_BUCKET", "gai-community29oct-7500-composer-dags"
)
project_id = os.environ.get("_PROJECT_ID", "gai-community29oct-7500")
region = os.environ.get("_REGION", "europe-west1")
zone = os.environ.get("_ZONE", "europe-west1-b")
image_version = os.environ.get("_IMAGE", "2.2-debian12")
subnetwork_uri = os.environ.get(
    "_SUBNETWORK",
    f"projects/{project_id}/regions/{region}/subnetworks/default",
)
service_account = os.environ.get(
    "_SERVICE_ACCOUNT",
    f"composer-worker-sa@{project_id}.iam.gserviceaccount.com",
)

# Compute Engine machine & disk sizing
master_machine_type = os.environ.get("_MASTER_MACHINE", "n2-standard-4")
worker_machine_type = os.environ.get("_WORKER_MACHINE", "n2-standard-4")
master_disk_size = int(os.environ.get("_MASTER_DISK_SIZE", "100"))
worker_disk_size = int(os.environ.get("_WORKER_DISK_SIZE", "200"))
num_workers = int(os.environ.get("_WORKER_NUMBER", "2"))
num_preemptible_workers = int(os.environ.get("_WORKER_PREEMPTIBLE_NUMBER", "0"))
idle_delete_ttl = int(os.environ.get("_MAX_IDLE", "1800"))

# Spark BigQuery Connector JAR and firewall tags
jar_spark_location = os.environ.get(
    "_SPARK_JAR",
    "gs://spark-lib/bigquery/spark-bigquery-with-dependencies_2.12-0.36.1.jar",
)
tags = convert_string_to_list(
    os.environ.get(
        "_TAGS",
        "allow-internal-dataproc-dev allow-ssh-from-management-zone-dev",
    )
)

# ==============================================================================
# 3. DAG Schedule, Naming & GCS Artifact Paths
# ==============================================================================
schedule_interval = os.environ.get("_SCHEDULER", "@daily")

environment_type = os.environ.get("_ENV", "dev")
lm = os.environ.get("_LOCAL_MARKET", "es")
release = os.environ.get("_RELEASE", "r2")
goal = os.environ.get("_GOAL", "spark_transformations")

# Standardized enterprise naming convention: <goal>-<release>-<market>-<env>
dag_name = f"{goal}-{release}-{lm}-{environment_type}"
dag_folder_name = f"{goal}_{release}_{lm}_{environment_type}"
cluster_name = f"{goal.replace('_', '-')}-target-{{{{ ds_nodash }}}}"

# GCS folder location where `utils/add_dags_to_composer.py` uploads the job & zip
code_files = f"gs://{storage_bucket}/dags/{dag_folder_name}"

# HCFS URI of the main PySpark driver script
run_main = f"{code_files}/{dag_folder_name}_job.py"

# Additional files & packaged Python modules (`utils.zip`) distributed to workers
# NOTE: Dataproc unpacks `.zip` archives into the working directory; `utils.zip`
# contains `utils/utils.py` from Part 1 (`dataproc-workshop`).
run_files = [code_files]
run_pyfiles = [f"{code_files}/utils.zip"]

# Deterministic Airflow task IDs
safe_dag_suffix = dag_name.replace("-", "_")
create_task_id = f"create_cluster_{safe_dag_suffix}"
run_task_id = f"run_pyspark_job_{safe_dag_suffix}"
delete_task_id = f"delete_cluster_{safe_dag_suffix}"

# GCP resource labels for cost attribution and governance
labels = {
    "project-cluster-env": environment_type,
    "project-goal": goal.replace("_", "-"),
    "project-cluster-owner": "eilinlux-gmail-com",
    "project-team-tag": "data-engineers",
}

# ==============================================================================
# 4. Ephemeral Dataproc Cluster Configuration Dictionary
# ==============================================================================
CLUSTER_CONFIG = {
    "temp_bucket": storage_bucket,
    "gce_cluster_config": {
        "zone_uri": zone,
        "subnetwork_uri": subnetwork_uri,
        "internal_ip_only": True,
        "service_account": service_account,
        "tags": tags,
        "metadata": {"enable-oslogin": "true"},
    },
    "master_config": {
        "num_instances": 1,
        "machine_type_uri": master_machine_type,
        "disk_config": {
            "boot_disk_type": "pd-standard",
            "boot_disk_size_gb": master_disk_size,
        },
    },
    "worker_config": {
        "num_instances": num_workers,
        "machine_type_uri": worker_machine_type,
        "disk_config": {
            "boot_disk_type": "pd-standard",
            "boot_disk_size_gb": worker_disk_size,
        },
    },
    "secondary_worker_config": {
        "num_instances": num_preemptible_workers,
        "is_preemptible": True,
    },
    "software_config": {
        "image_version": image_version,
        "properties": {
            "core:fs.gs.implicit.dir.repair.enable": "false",
            "core:fs.gs.status.parallel.enable": "true",
            "dataproc:dataproc.logging.stackdriver.job.driver.enable": "true",
            "dataproc:am.primary_only": "true",
            "spark:spark.jars": jar_spark_location,
        },
    },
    "lifecycle_config": {
        "idle_delete_ttl": {"seconds": idle_delete_ttl},
    },
    # Enable Dataproc Component Gateway (HTTP port access to Spark History Server / YARN UI)
    "endpoint_config": {
        "enable_http_port_access": True,
    },
}

# PySpark job payload for `DataprocSubmitJobOperator`
PYSPARK_JOB = {
    "reference": {"project_id": project_id},
    "placement": {"cluster_name": cluster_name},
    "pyspark_job": {
        "main_python_file_uri": run_main,
        "python_file_uris": run_pyfiles,
        "file_uris": run_files,
        "jar_file_uris": [jar_spark_location],
        "args": ["--start", str(start), "--end", str(end)],
    },
}

# ==============================================================================
# 5. Airflow Default Arguments & DAG Definition
# ==============================================================================
default_dag_args = {
    "owner": "Eilin Lux",
    "start_date": datetime.datetime(2025, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
    "project_id": project_id,
}

with models.DAG(
    dag_id=dag_name,
    schedule=schedule_interval,
    catchup=False,
    default_args=default_dag_args,
    tags=["dataproc", "pyspark", "cicd", environment_type, lm],
) as dag:

    # Step 1: Provision the ephemeral Dataproc cluster with Component Gateway enabled
    create_cluster_task = DataprocCreateClusterOperator(
        task_id=create_task_id,
        project_id=project_id,
        region=region,
        cluster_name=cluster_name,
        cluster_config=CLUSTER_CONFIG,
        labels=labels,
    )

    # Step 2: Submit the PySpark transformation job along with `utils.zip`
    run_job_task = DataprocSubmitJobOperator(
        task_id=run_task_id,
        project_id=project_id,
        region=region,
        job=PYSPARK_JOB,
    )

    # Step 3: Always tear down the ephemeral cluster (even if the Spark job fails)
    delete_cluster_task = DataprocDeleteClusterOperator(
        task_id=delete_task_id,
        project_id=project_id,
        region=region,
        cluster_name=cluster_name,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    # Define linear pipeline execution order
    create_cluster_task >> run_job_task >> delete_cluster_task