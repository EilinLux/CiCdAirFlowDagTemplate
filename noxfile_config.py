# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Nox test configuration override for Cloud Composer CI/CD DAG validation.

Note: Primary dependency management and testing in this repository use `uv`
(`pyproject.toml` + `uv run pytest`). This file is preserved for compatibility
with Google Cloud Python samples Nox test runners.
"""

import tempfile

# Airflow initializes configuration files inside `AIRFLOW_HOME` on import, so we
# point `AIRFLOW_HOME` to an isolated temporary directory during test runs.
_tmpdir = tempfile.TemporaryDirectory()

TEST_CONFIG_OVERRIDE = {
    # Ignore legacy Python versions no longer supported by Cloud Composer 2 / Airflow 2.10
    "ignored_versions": [
        "2.7",
        "3.6",
        "3.7",
        "3.8",
        "3.9",
    ],
    "enforce_type_hints": True,
    "gcloud_project_env": "GOOGLE_CLOUD_PROJECT",
    "pip_version_override": None,
    # Inject isolated AIRFLOW_HOME for deterministic test execution
    "envs": {"AIRFLOW_HOME": _tmpdir.name},
}
