"""
olist_ingestion_dag
--------------------
Downloads the Kaggle Olist dataset and lands it as Parquet in GCS
(gs://<bucket>/raw/<table>/...). This is the only DAG on a time schedule;
everything downstream is triggered off the GCS dataset it produces.
"""
from __future__ import annotations

import datetime

from airflow import DAG
from airflow.datasets import Dataset
from airflow.models import Variable

from operators.dlt_operator import DltKaggleToGCSOperator

GCS_BUCKET = Variable.get("gcs_bucket", default_var="olist-airflow")
GCP_PROJECT_ID = Variable.get("gcp_project_id", default_var="")

RAW_DATASET = Dataset(f"gs://{GCS_BUCKET}/raw")

default_args = {
    "owner": "abbas.billiamin",
    "retries": 2,
    "retry_delay": datetime.timedelta(minutes=5),
}

with DAG(
    dag_id="olist_ingestion_dag",
    description="Kaggle Olist CSVs -> GCS bronze landing (via dlt)",
    schedule="0 3 * * *",  # daily 03:00   
    start_date=datetime.datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["olist", "ingestion", "bronze"],
) as dag:

    load_kaggle_to_gcs = DltKaggleToGCSOperator(
        task_id="load_kaggle_to_gcs",
        gcs_bucket=GCS_BUCKET,
        gcp_project_id=GCP_PROJECT_ID,
        outlets=[RAW_DATASET],
    )