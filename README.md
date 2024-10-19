# Airflow DAG Deployment Template

This repository provides a template for setting up, deploying, and testing Apache Airflow DAGs (Directed Acyclic Graphs) using Google Cloud Composer. It leverages CI/CD principles to automate the deployment process and ensure consistency.

## Table of Contents

- [Key Concepts](#key-concepts)
    - [Airflow](#airflow)
    - [Composer](#composer)
    - [CI/CD](#ci-cd)
- [Repository Structure](#repository-structure)
- [Usage](#usage)
- [Environment Variables](#environment-variables)
    - [Project-Related](#project-related)
    - [DAG-Related](#dag-related)
    - [Optional](#optional)

## Key Concepts

### Airflow

Airflow is an open-source platform to programmatically author, schedule, and monitor workflows. Workflows are defined as DAGs, which consist of individual tasks arranged with dependencies and data flows.

For more information, see the [Airflow documentation](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/index.html).

### Composer

Cloud Composer is a fully managed workflow orchestration service built on Apache Airflow. It allows you to create and run Airflow workflows without managing the underlying infrastructure.

### CI/CD

Continuous Integration and Continuous Delivery (CI/CD) automates the software development lifecycle. This template uses CI/CD to:

- **Continuous Integration:** Merge code changes frequently to a shared mainline.
- **Continuous Delivery:** Automatically deploy DAGs to a testing or production environment.

## Repository Structure

├── dags
│   └── spark_transformations
│       ├── spark_transformations_job.py
│       └── utils.zip
└── utils
└── add_dags_to_composer.py


- **`add-dags-to-composer.cloudbuild.yaml`:** Cloud Build configuration file for installing dependencies and running the deployment script.
- **`utils/add_dags_to_composer.py`:** Python script to add DAGs to your Composer environment and provide utility functions (e.g., zipping files).
- **`dags/`:**  Directory containing DAGs and related files.
    - **`GOALNAME-dag.py`:**  Configures DAG creation, job execution, and DAG deletion.
    - **`GOALNAME/`:**  Contains the job file (`GOALNAME_job.py`) and zipped utilities (`utils.zip`).

## Usage

This template provides a starting point for deploying your Airflow DAGs to Cloud Composer. You can customize it to fit your specific needs.

1. **Clone the repository:**

   ```bash
   git clone [your-repository-url]
   ```
2. Update the DAGs and configuration files:

  Modify the GOALNAME-dag.py file to define your DAG's schedule, tasks, and dependencies.
  Update the GOALNAME_job.py file with your job's logic.
  Adjust the add-dags-to-composer.py script if needed.
3. Set environment variables:
    Configure the required environment variables (see the next section).
4. Use Cloud Build for deployment:
    Set up a Cloud Build trigger to automatically deploy your DAGs on code changes.
### Environment Variables
  **Project-Related**
    _DAGS_DIRECTORY: Location of your DAGs within the repository (e.g., dags).
    _DAGS_BUCKET: Cloud Storage bucket to store the DAG code.
    _WORKER_POOL: Name of the worker pool in your Composer environment.
    _PROJECT_ID: Your Google Cloud project ID.
    _REGION: Region of your Composer environment (e.g., europe-west1).
    _ZONE: Zone within the region (e.g., europe-west1-b).
    _SUBNETWORK: Subnetwork for the Composer environment (e.g., projects/PROJECT_ID/regions/REGION/subnetworks/SUBNETWORK_NAME).
    _SERVICE_ACCOUNT: Service account for the Composer environment (e.g., PROJECT_ID-comp-sa@PROJECT_ID.iam.gserviceaccount.com).
  **DAG-Related**
    _IMAGE: Dataproc image version (e.g., 1.5.53-debian10).
    _MASTER_MACHINE: Machine type for the Dataproc master node.
    _WORKER_MACHINE: Machine type for the Dataproc worker nodes.
    _MASTER_DISK_SIZE: Disk size for the master node.
    _WORKER_DISK_SIZE: Disk size for the worker nodes.
    _WORKER_NUMBER: Number of worker nodes.
    _WORKER_PREEMPTIBLE_NUMBER: Number of preemptible worker nodes.
    _MAX_IDLE: Maximum idle time for the Dataproc cluster.
    _TAGS: List of tags to attach to the Dataproc instances (e.g., ['allow-internal-dataproc-dev', 'allow-ssh-from-management-zone-dev']).
    _SCHEDULER: Scheduler configuration for the DAG.
  **Optional**
    _GOAL: Name or identifier for the DAG (e.g., spark_transformations).
    _ENV: Environment (e.g., dev).
    _LOCAL_MARKET: Local market or region (e.g., es).
    _RELEASE: Release version (e.g., r1, r2).
    _SPARK_JAR: Path to a Spark JAR file (e.g., gs://spark-lib/bigquery/spark-bigquery-latest_2.12.jar).
