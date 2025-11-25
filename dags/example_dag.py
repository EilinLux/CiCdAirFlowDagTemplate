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

"""Baseline Smoke-Test DAG (`composer_sample_dag`) for Cloud Composer CI/CD.

This lightweight DAG verifies that Cloud Composer can parse, schedule, and run
a simple `BashOperator` task that echoes the active `dag_run.id`. It serves as
a fast canary check during CI/CD pipeline validation.
"""

import datetime

from airflow import models
from airflow.operators.bash import BashOperator

# Static reference start date (best practice for deterministic Airflow scheduling)
START_DATE = datetime.datetime(2025, 1, 1)

# Default task-level configuration applied to all operators in this DAG
default_args = {
    "owner": "Composer CI/CD Example",
    "depends_on_past": False,
    "email": [""],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
    "start_date": START_DATE,
}

with models.DAG(
    dag_id="composer_sample_dag",
    catchup=False,
    default_args=default_args,
    schedule=datetime.timedelta(days=1),
    tags=["cicd", "smoke-test", "sample"],
) as dag:
    # Print the active dag_run ID to the Airflow task logs
    print_dag_run_conf = BashOperator(
        task_id="print_dag_run_conf",
        bash_command="echo {{ dag_run.id }}",
    )
