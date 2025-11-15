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

"""Shared unit testing utilities for validating Apache Airflow DAG modules in CI.

This module provides `assert_has_valid_dag(module)`, which inspects a loaded
Python DAG module and verifies:
  1. At least one `airflow.models.DAG` object is defined in the module.
  2. Every discovered DAG has at least one task registered.
  3. Every discovered DAG is a valid Directed Acyclic Graph (zero dependency cycles)
     using Airflow's built-in `check_cycle` utility.
"""

from types import ModuleType
from typing import List

from airflow import models
from airflow.utils.dag_cycle_tester import check_cycle


def extract_dags_from_module(module: ModuleType) -> List[models.DAG]:
    """Return all `airflow.models.DAG` instances defined in the given Python module."""
    return [
        attr
        for attr in vars(module).values()
        if isinstance(attr, models.DAG)
    ]


def assert_has_valid_dag(module: ModuleType) -> None:
    """Assert that a Python module defines at least one valid, cycle-free Airflow DAG.

    Args:
        module: The imported Python module containing one or more Airflow DAGs.

    Raises:
        AssertionError: If no `DAG` instance is found or if a DAG contains zero tasks.
        AirflowDagCycleException: If any task dependency cycle is detected.
    """
    dags = extract_dags_from_module(module)
    assert len(dags) > 0, (
        f"Module '{module.__name__}' does not contain any airflow.models.DAG instances."
    )

    for dag in dags:
        # Verify the DAG has at least one task registered
        assert len(dag.tasks) > 0, (
            f"DAG '{dag.dag_id}' in '{module.__name__}' has no tasks defined."
        )
        # Verify the DAG has no circular task dependencies
        check_cycle(dag)
