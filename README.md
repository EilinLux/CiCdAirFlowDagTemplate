## Key concepts:

### AirFlow
Airflow is a platform that lets you build and run workflows. A workflow is represented as a DAG (a Directed Acyclic Graph), and contains individual pieces of work called Tasks, arranged with dependencies and data flows taken into account. More: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/index.html 

### Composer
Cloud Composer is built on the popular Apache Airflow open source project and operates using the Python programming language. By using Cloud Composer instead of a local instance of Apache Airflow, you can benefit from the best of Airflow with no installation or management overhead.


### ci-cd 
In software engineering, it is the combined practices of continuous integration and continuous delivery or continuous deployment. 
In our case the two following applies :
1) continuous integration as the practice of merging all developers' working copies to a shared mainline as often as possible.
2) continuous delivery as the practice of automatically deploy all code changes to a testing and/or production environment after the build stage.
3) continuous deployment every change that passes all stages of your production pipeline is released to customers without human intervention.


## Usage for this repo 

This repo is a template to set up deploy and test of DAG and Jobs 

### folder structure 
1) add-dags-to-composer.cloudbuild.yaml: install dependencies and run utils/add_dags_to_composer.py
2) /utils/add_dags_to_composer.py: called by add-dags-to-composer.cloudbuild.yaml, contains python script to add your dags in /dags folder to your enviroment and additional utils code (ex. zip files)
3) /dags folder contains
*  file to configure dag creation, job exection and  dag deletion (GOALNAME-dag.py)
*  folder (GOALNAME) that contains the job (GOALNAME/GOALNAME_job.py) and zipped utils (GOALNAME/utils.zip)

# Environment variables
Environment variables, as the name suggests, are variables in your system that describe your environment. 

#### project related
*  _DAGS_DIRECTORY:   dags location for your AirFlow 
*  _DAGS_BUCKET:  location on gcp Cloud Storage bucket that should store the code
* _WORKER_POOL
* _PROJECT_ID
* _REGION (ex. 'europe-west1')
* _ZONE (ex. 'europe-west1-b'
* _SUBNETWORK (ex. 'projects/PROJECT_ID/regions/REGION/subnetworks/SUBNETWORK_NAME')
* _SERVICE_ACCOUNT (ex. 'PROJECT_ID-comp-sa@PROJECT_ID.iam.gserviceaccount.com')

#### DAG related (More info: https://airflow.apache.org/docs/apache-airflow/1.10.3/_api/airflow/contrib/operators/dataproc_operator/index.html)
* _IMAGE (ex. '1.5.53-debian10')
* _MASTER_MACHINE
* _WORKER_MACHINE
* _MASTER_DISK_SIZE
* _WORKER_DISK_SIZE
* _WORKER_NUMBER
* _WORKER_PREEMPTIBLE_NUMBER # num-secondary-workers more info: https://cloud.google.com/dataproc/docs/concepts/compute/secondary-vms
* _MAX_IDLE
* _TAGS  (ex. ['allow-internal-dataproc-dev', 'allow-ssh-from-management-zone-dev']) Specifies strings to be attached to the instance for later identifying the instance when adding network firewall rules, it can be a list, 
* _SCHEDULER

####  [Optinal]  but set in this demo
* _GOAL (ex. spark_transformations)
* _ENV (ex. "dev")
* _LOCAL_MARKET (ex. 'es')
* _RELEASE  (ex. r1, r2, ...) 
* _SPARK_JAR (ex.'gs://spark-lib/bigquery/spark-bigquery-latest_2.12.jar'), if need to have it static 



