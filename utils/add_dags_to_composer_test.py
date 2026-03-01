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

"""Unit tests for `utils/add_dags_to_composer.py`.

Validates:
  1. `_create_dags_list` raises `FileNotFoundError` on missing directories.
  2. `_create_dags_list` returns empty results for empty directories.
  3. `_create_dags_list` includes all 3 production DAGs (`example_dag.py`,
     `example2_dag.py`, `spark_transformations_r2_es_dev_dag.py`) while
     filtering out `*_test.py`, `__init__.py`, and `internal_unit_testing.py`.
  4. `_create_zip_folder_list` discovers nested PySpark job scripts and `utils.zip`.
  5. `upload_dags_to_composer` and `upload_zip_folders_to_composer` upload the
     expected blobs to Google Cloud Storage.
"""

import os
import pathlib
from shutil import copytree
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from utils import add_dags_to_composer

DAGS_DIR = pathlib.Path(__file__).resolve().parent.parent / "dags"


@pytest.fixture(scope="function")
def dags_directory() -> str:
    """Copy the contents of `dags/` to an isolated temporary directory."""
    temp_dir = tempfile.mkdtemp()
    copytree(DAGS_DIR, f"{temp_dir}/", dirs_exist_ok=True)
    yield temp_dir


@pytest.fixture(scope="function")
def empty_directory() -> str:
    """Provide an empty temporary directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir


def test_create_dags_list_invalid_directory() -> None:
    """Verify `_create_dags_list` raises FileNotFoundError when directory is missing."""
    with pytest.raises(FileNotFoundError):
        add_dags_to_composer._create_dags_list("this-directory-does-not-exist/")


def test_create_dags_list_empty_directory(empty_directory: str) -> None:
    """Verify `_create_dags_list` returns an empty list for an empty directory."""
    temp_dir, dags = add_dags_to_composer._create_dags_list(empty_directory)
    assert len(dags) == 0
    assert len(os.listdir(temp_dir)) == 0


def test_create_dags_list(dags_directory: str) -> None:
    """Verify only production DAG files are kept and all test/helper files are excluded."""
    temp_dir, dags = add_dags_to_composer._create_dags_list(dags_directory)
    assert len(dags) == 3
    assert f"{temp_dir}/example_dag.py" in dags
    assert f"{temp_dir}/example2_dag.py" in dags
    assert f"{temp_dir}/spark_transformations_r2_es_dev_dag.py" in dags

    # Verify excluded files are never deployed to Cloud Composer
    assert f"{temp_dir}/__init__.py" not in dags
    assert f"{temp_dir}/internal_unit_testing.py" not in dags
    assert f"{temp_dir}/example_dag_test.py" not in dags
    assert f"{temp_dir}/example2_dag_test.py" not in dags
    assert f"{temp_dir}/spark_transformations_r2_es_dev_dag_test.py" not in dags


def test_create_zip_folder_list(dags_directory: str) -> None:
    """Verify nested PySpark job scripts and `utils.zip` are discovered for upload."""
    temp_dir, nested_files = add_dags_to_composer._create_zip_folder_list(dags_directory)
    rel_paths = [os.path.relpath(p, temp_dir).replace("\\", "/") for p in nested_files]
    assert "spark_transformations_r2_es_dev/spark_transformations_r2_es_dev_job.py" in rel_paths
    assert "spark_transformations_r2_es_dev/utils.zip" in rel_paths


def test_upload_dags_to_composer_no_files(
    capsys: pytest.CaptureFixture, empty_directory: str
) -> None:
    """Verify graceful output when there are no DAGs in the directory."""
    add_dags_to_composer.upload_dags_to_composer(empty_directory, "mock-composer-bucket")
    out, _ = capsys.readouterr()
    assert "No DAGs to upload." in out


@patch("utils.add_dags_to_composer.storage.Client")
def test_upload_dags_to_composer(
    mock_storage_client: MagicMock, capsys: pytest.CaptureFixture
) -> None:
    """Verify `upload_dags_to_composer` uploads each DAG file to `dags/<filename>` in GCS."""
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_storage_client.return_value.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    add_dags_to_composer.upload_dags_to_composer(str(DAGS_DIR), "mock-composer-bucket")
    out, _ = capsys.readouterr()

    assert "uploaded to mock-composer-bucket/dags/example_dag.py" in out
    assert "uploaded to mock-composer-bucket/dags/spark_transformations_r2_es_dev_dag.py" in out
    assert mock_blob.upload_from_filename.call_count == 3


@patch("utils.add_dags_to_composer.storage.Client")
def test_upload_zip_folders_to_composer(
    mock_storage_client: MagicMock, capsys: pytest.CaptureFixture
) -> None:
    """Verify `upload_zip_folders_to_composer` uploads `utils.zip` and the PySpark job."""
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_storage_client.return_value.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    add_dags_to_composer.upload_zip_folders_to_composer(
        str(DAGS_DIR), "mock-composer-bucket"
    )
    out, _ = capsys.readouterr()

    assert "dags/spark_transformations_r2_es_dev/utils.zip" in out
    assert "dags/spark_transformations_r2_es_dev/spark_transformations_r2_es_dev_job.py" in out
