"""
olist_bq_load_dag
------------------
Loads the Parquet files dlt landed in GCS into native BigQuery bronze tables
(one external-load job per table, run in parallel). Triggered automatically
when olist_ingestion_dag's outlet dataset is updated (dataset-aware scheduling)
-- no cron needed here.
"""
from __future__ import annotations

import datetime

from airflow import DAG
from airflow.datasets import Dataset
from airflow.models import Variable
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import (
    GCSToBigQueryOperator,
)

GCS_BUCKET = Variable.get("gcs_bucket", default_var="olist-airflow")
BQ_BRONZE_DATASET = Variable.get("bq_bronze_dataset", default_var="olist_bronze")

RAW_DATASET = Dataset(f"gs://{GCS_BUCKET}/raw")
BRONZE_DATASET = Dataset(f"bq://{BQ_BRONZE_DATASET}")

TABLES = [
    "orders",
    "order_items",
    "order_payments",
    "order_reviews",
    "products",
    "customers",
    "sellers",
    "geolocation",
    "product_category_translation",
]

default_args = {
    "owner": "abbas.billiamin",
    "retries": 2,
    "retry_delay": datetime.timedelta(minutes=5),
}

with DAG(
    dag_id="olist_bq_load_dag",
    description="GCS raw Parquet -> BigQuery bronze tables",
    schedule=[RAW_DATASET],  # dataset-triggered, not cron
    start_date=datetime.datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["olist", "load", "bronze"],
) as dag:

    for table in TABLES:
        GCSToBigQueryOperator(
            task_id=f"load_{table}_to_bronze",
            bucket=GCS_BUCKET,
            source_objects=[f"raw/olist_raw/{table}/*.parquet"],
            source_format="PARQUET",
            destination_project_dataset_table=f"{BQ_BRONZE_DATASET}.{table}",
            write_disposition="WRITE_TRUNCATE",
            create_disposition="CREATE_IF_NEEDED",
            autodetect=True,
            outlets=[BRONZE_DATASET] if table == TABLES[-1] else [],
        )
