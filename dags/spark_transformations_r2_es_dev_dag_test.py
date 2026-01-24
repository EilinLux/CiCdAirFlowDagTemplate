"""Unit tests for `dags/spark_transformations_r2_es_dev_dag.py` and its PySpark driver job.

Validates:
  1. The `spark_transformations-r2-es-dev` DAG loads cleanly with zero cycles.
  2. The 3-step ephemeral Dataproc task chain (`create_cluster >> run_pyspark_job >> delete_cluster`)
     is properly wired and `delete_cluster` uses `TriggerRule.ALL_DONE`.
  3. The PySpark driver script (`spark_transformations_r2_es_dev_job.py`) extracts
     `utils.zip` and computes retail sales net revenue metrics using `utils.utils`.
"""

from airflow.utils.trigger_rule import TriggerRule

from dags import internal_unit_testing, spark_transformations_r2_es_dev_dag
from dags.spark_transformations_r2_es_dev import spark_transformations_r2_es_dev_job


def test_spark_transformations_dag_integrity() -> None:
    """Verify DAG structure, task count, dependency order, and ALL_DONE teardown rule."""
    internal_unit_testing.assert_has_valid_dag(spark_transformations_r2_es_dev_dag)

    dag = spark_transformations_r2_es_dev_dag.dag
    assert len(dag.tasks) == 3

    create_task = dag.get_task(spark_transformations_r2_es_dev_dag.create_task_id)
    run_task = dag.get_task(spark_transformations_r2_es_dev_dag.run_task_id)
    delete_task = dag.get_task(spark_transformations_r2_es_dev_dag.delete_task_id)

    # Verify linear dependency chain: create -> run -> delete
    assert run_task.task_id in create_task.downstream_task_ids
    assert delete_task.task_id in run_task.downstream_task_ids

    # Verify cluster teardown runs even if the PySpark job fails
    assert delete_task.trigger_rule == TriggerRule.ALL_DONE


def test_spark_transformations_job_execution() -> None:
    """Verify the PySpark driver script unpacks `utils.zip` and calculates net revenue."""
    result = spark_transformations_r2_es_dev_job.run(
        ["--start", "2025-10-01", "--end", "2025-10-07"]
    )
    assert "some_utility_function" in result["banner"]
    assert result["start_date"] == "2025-10-01"
    assert result["end_date"] == "2025-10-07"
    assert result["category_totals"]["Electronics"] == 3000.0
    assert result["category_totals"]["Apparel"] == 300.0
