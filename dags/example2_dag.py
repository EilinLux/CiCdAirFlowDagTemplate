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

"""Secondary Smoke-Test DAG (`composer_sample_dag_2`) for Multi-DAG CI/CD Sync.

This second sample DAG validates that `utils/add_dags_to_composer.py` discovers
and synchronizes multiple DAG files in `dags/` while properly excluding test
modules (`*_test.py`) and helper packages.
"""

import datetime

from airflow import models
from airflow.operators.bash import BashOperator

START_DATE = datetime.datetime(2025, 1, 1)

default_args = {
    "owner": "Composer CI/CD Example 2",
    "depends_on_past": False,
    "email": [""],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
    "start_date": START_DATE,
}

with models.DAG(
    dag_id="composer_sample_dag_2",
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
