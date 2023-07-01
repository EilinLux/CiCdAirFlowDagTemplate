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

1) add-dags-to-composer.cloudbuild.yaml add the dag in /dags folder to your enviroment, to make it work add in the cloudbuild _DAGS_DIRECTORY and _DAGS_BUCKET.
