"""
author: Zelda Ailine Luconi
email: eilinlux@gmail.com

"""
import datetime
import os
from airflow import models
from airflow.contrib.operators import dataproc_operator
from airflow.utils import trigger_rule
from airflow.operators import bash_operator

def convert_string_to_list(string):
    li = list(string.split(" "))
    return li
  

#############################################
######## DAG VARIABLES ######################
#############################################



### DateTime cluster specifications 
#############################################
start = {{ yesterday_ds_nodash }} # the day before the execution date as YYYY-MM-DD
end = {{ execution_date }} # the day of the execution date as YYYY-MM-DD

# creates a datetime object from the given string.
my_date = datetime.strptime(end, "%Y-%m-%d")

year = end.year
month = end.month
day = end.day

### Dataproc cluster specifications 
#############################################
storage_bucket = os.environ.get("_DAGS_BUCKET")

region=os.environ.get("_REGION")#'europe-west1'
zone=os.environ.get("_ZONE")#'europe-west1-b'
image_version =os.environ.get("_IMAGE")#'1.5.53-debian10'
subnetwork_uri=os.environ.get("_SUBNETWORK")# 'projects/PROJECT_ID/regions/REGION/subnetworks/SUBNETWORK_NAME'
project_id = os.environ.get("_PROJECT_ID")
service_account= os.environ.get("_SERVICE_ACCOUNT") #'PROJECT_ID-comp-sa@PROJECT_ID.iam.gserviceaccount.com'
master_machine_type=os.environ.get("_MASTER_MACHINE")
worker_machine_type=os.environ.get("_WORKER_MACHINE")
master_disk_size = os.environ.get("_MASTER_DISK_SIZE")
worker_disk_size = os.environ.get("_WORKER_DISK_SIZE")
num_workers= os.environ.get("_WORKER_NUMBER")
num_preemptible_workers = os.environ.get("_WORKER_PREEMPTIBLE_NUMBER") # num-secondary-workers more info: https://cloud.google.com/dataproc/docs/concepts/compute/secondary-vms
idle_delete_ttl = os.environ.get("_MAX_IDLE")# max-idle seconds equals to 14 h
jar_spark_location = os.environ.get("_SPARK_JAR") # if need to have it static 'gs://spark-lib/bigquery/spark-bigquery-latest_2.12.jar'
tags= convert_string_to_list(os.environ.get("_TAGS")) # Specifies strings to be attached to the instance for later identifying the instance when adding network firewall rules, it can be a list, ex. ['allow-internal-dataproc-dev', 'allow-ssh-from-management-zone-dev']
### Scheduler interval
#############################################
schedule_interval=os.environ.get("_SCHEDULER")

### Spark Job naming
#############################################
environment_type = os.environ.get("_ENV") # "dev"
lm = os.environ.get("_LOCAL_MARKET")  # 'it'
release=os.environ.get("_RELEASE") # r2
goal=os.environ.get("_GOAL")
dag_name = '{}-{}-{}-{}'.format(goal, release, lm, environment_type)
cluster_name='{}-target-{}-{}-{}'.format(goal,year, month, day)



### Storage bucket specifications (where the code is saved)
#############################################

# [Required] Folder location of your code
code_files = 'gs://{}/{}'.format(storage_bucket, dag_name) 

# [Required] The Hadoop Compatible Filesystem (HCFS) URI of the main Python file to use as the driver. Must be a .py file.
run_main='{}/{}_job.py'.format(code_files, goal.replace("-","_"))

# [Opional] Cloud Storage specifications (not mandatory)
    # List of files to be copied to the working directory
run_files=[ '{}'.format(code_files) ]
    # List of Python files to pass to the PySpark framework. Supported file types: .py, .egg, and .zip
run_pyfiles=['{}/utils.zip'.format(code_files)] 

# NOTE: in this example a zip file has been used, 
# it will unpack without extracting the file in an omonimous folder, 
# therefore be careful on the imports. 



### Task ids specifications 
#############################################
create_task_id='create_cluster_{}'.format(dag_name.replace("-","_"))
run_task_id = 'run_pyspark_job_{}'.format(dag_name.replace("-","_"))
delete_task_id='delete_cluster_{}'.format(dag_name.replace("-","_"))


## labeling 
#############################################
labels={
        "project-cluster-env":environment_type,
        "project-goal":goal,
        "project-cluster-owner":"eilinlux-gmail_com",
        "project-team-tag":"data_engineers"
     }


#############################################
######## DAG DEFAULT ########################
#############################################
default_dag_args = {
    'start_date': datetime.datetime(2015, 12, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': datetime.timedelta(minutes=5),
    'project_id': project_id,
    'year':year,
    'month':month,
    'day':day,
    'code_files':code_files,
    'start':start,
    'end':end
}


#############################################
######## DAG MODEL ##########################
#############################################

with models.DAG(
        dag_name,
        schedule_interval=schedule_interval,
        default_args=default_dag_args) as dag:
    
    # override cluster creation to enable getway component
    class CustomDataprocClusterCreateOperator(dataproc_operator.DataprocClusterCreateOperator):
        def __init__(self, *args, **kwargs):
            super(CustomDataprocClusterCreateOperator, self).__init__(*args, **kwargs)
        def _build_cluster_data(self):
            cluster_data = super(CustomDataprocClusterCreateOperator, self)._build_cluster_data()
            cluster_data['config']['endpointConfig'] = {
            'enableHttpPortAccess': True
            }
            # cluster_data['config']['softwareConfig']['optionalComponents'] = [ 'JUPYTER', 'ANACONDA' ]
            return cluster_data

    #Create features creation Dataproc cluster.
    create_cluster_task = CustomDataprocClusterCreateOperator(
        task_id=create_task_id,
        project_id=project_id,
        cluster_name=cluster_name,
        storage_bucket=storage_bucket,
        region=region, 
        zone=zone,
        service_account=service_account,
        subnetwork_uri=subnetwork_uri,
        labels=labels, 
        tags=tags,
        master_machine_type=master_machine_type,
        master_disk_size=master_disk_size,
        num_workers=num_workers,
        worker_machine_type=worker_machine_type,
        worker_disk_size=worker_disk_size,
        num_preemptible_workers=num_preemptible_workers,
        image_version=image_version,
        idle_delete_ttl=idle_delete_ttl,
        internal_ip_only=True,
        metadata={'enable-oslogin': 'true'},
        properties={
            'core:fs.gs.implicit.dir.repair.enable':'false', 
            'core:fs.gs.status.parallel.enable':'true',
            'dataproc:dataproc.logging.stackdriver.job.driver.enable':'true', 
            'dataproc:am.primary_only':'true', 
            'spark:spark.jars' : jar_spark_location}
        )
    
    # Run the Spark Job
    run_job_task = dataproc_operator.DataProcPySparkOperator(
        task_id=run_task_id,
        main=run_main,
        files=run_files,  
        pyfiles=run_pyfiles,
        cluster_name=cluster_name,
        region=region,
        arguments=['--start', str(start), '--end', str(end)],
        dataproc_pyspark_jars=jar_spark_location
    )

    # Delete Cloud Dataproc cluster.
    delete_cluster_task = dataproc_operator.DataprocClusterDeleteOperator(
       task_id=delete_task_id,
       cluster_name=cluster_name,
       region=region, 
       trigger_rule=trigger_rule.TriggerRule.ALL_DONE
    )

    
    # Define DAG dependencies.
    create_cluster_task >> run_job_task >> delete_cluster_task 

      