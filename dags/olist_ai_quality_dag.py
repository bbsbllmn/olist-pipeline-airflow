"""
olist_ai_quality_dag
----------------------
Runs statistical + LLM-narrated anomaly detection over the gold marts, right
after dbt build finishes. Posts findings to Slack (if configured) and always
logs the summary to the task output for visibility in the Airflow UI.
"""
from __future__ import annotations

import datetime

from airflow import DAG
from airflow.datasets import Dataset
from airflow.models import Variable
from airflow.operators.python import PythonOperator

GCP_PROJECT_ID = Variable.get("gcp_project_id", default_var="")
BQ_GOLD_DATASET = Variable.get("bq_gold_dataset", default_var="olist_gold")

GOLD_DATASET = Dataset(f"bq://{BQ_GOLD_DATASET}")

default_args = {
    "owner": "abbas.billiamin",
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
}


def _run_anomaly_checks(**context):
    from include.ai.anomaly_detector import run

    summary = run(project=GCP_PROJECT_ID, gold_dataset=BQ_GOLD_DATASET)
    context["ti"].xcom_push(key="anomaly_summary", value=summary)
    return summary


with DAG(
    dag_id="olist_ai_quality_dag",
    description="AI-driven anomaly detection over gold marts",
    schedule=[GOLD_DATASET],
    start_date=datetime.datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["olist", "ai", "quality"],
) as dag:

    run_anomaly_checks = PythonOperator(
        task_id="run_anomaly_checks",
        python_callable=_run_anomaly_checks,
    )
