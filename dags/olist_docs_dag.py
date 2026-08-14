"""
olist_docs_dag
----------------
Turns the latest dbt manifest/run_results into a plain-English changelog via
LLM and posts it to Slack, so documentation stays current without a human
manually writing release notes for every model change.
"""
from __future__ import annotations

import datetime

from airflow import DAG
from airflow.datasets import Dataset
from airflow.models import Variable
from airflow.operators.python import PythonOperator

BQ_GOLD_DATASET = Variable.get("bq_gold_dataset", default_var="olist_gold")
GOLD_DATASET = Dataset(f"bq://{BQ_GOLD_DATASET}")

default_args = {
    "owner": "abbas.billiamin",
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
}


def _generate_and_post_changelog(**context):
    from include.ai.doc_summarizer import generate_changelog
    from include.ai.anomaly_detector import post_to_slack

    changelog = generate_changelog()
    post_to_slack(f"*dbt build changelog*\n{changelog}")
    context["ti"].xcom_push(key="changelog", value=changelog)
    return changelog


with DAG(
    dag_id="olist_docs_dag",
    description="AI-generated changelog summary of the latest dbt build",
    schedule=[GOLD_DATASET],
    start_date=datetime.datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["olist", "ai", "docs"],
) as dag:

    generate_and_post_changelog = PythonOperator(
        task_id="generate_and_post_changelog",
        python_callable=_generate_and_post_changelog,
    )
