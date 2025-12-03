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

"""Unit test for `dags/example_dag.py` (`composer_sample_dag`)."""

from dags import example_dag, internal_unit_testing


def test_dag_import() -> None:
    """Verify that `example_dag` loads without errors and has no task cycles."""
    internal_unit_testing.assert_has_valid_dag(example_dag)
    assert example_dag.dag.dag_id == "composer_sample_dag"
    assert example_dag.dag.catchup is False
