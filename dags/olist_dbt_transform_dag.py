"""
olist_dbt_transform_dag
------------------------
Runs `dbt build` (staging -> marts) against the bronze tables loaded by
olist_bq_load_dag, then generates dbt docs. Triggered by the bronze BQ
dataset being updated. On success, emits the gold dataset for downstream
AI quality checks / docs summarizer.
"""
from __future__ import annotations

import datetime

from airflow import DAG
from airflow.datasets import Dataset
from airflow.models import Variable
from airflow.operators.bash import BashOperator

BQ_BRONZE_DATASET = Variable.get("bq_bronze_dataset", default_var="olist_bronze")
BQ_GOLD_DATASET = Variable.get("bq_gold_dataset", default_var="olist_gold")

BRONZE_DATASET = Dataset(f"bq://{BQ_BRONZE_DATASET}")
GOLD_DATASET = Dataset(f"bq://{BQ_GOLD_DATASET}")

DBT_PROJECT_DIR = "/opt/airflow/dbt/olist_analytics"

default_args = {
    "owner": "abbas.billiamin",
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
}

with DAG(
    dag_id="olist_dbt_transform_dag",
    description="dbt build: bronze -> staging (silver) -> marts (gold)",
    schedule=[BRONZE_DATASET],
    start_date=datetime.datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["olist", "dbt", "silver", "gold"],
) as dag:

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt deps",
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            "dbt build --select staging marts --fail-fast"
        ),
        outlets=[GOLD_DATASET],
    )

    dbt_docs_generate = BashOperator(
        task_id="dbt_docs_generate",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt docs generate",
    )

    dbt_deps >> dbt_build >> dbt_docs_generate
