"""
Statistical anomaly detection over the gold marts, narrated in plain English
by an LLM. Runs after every dbt build.

Approach:
1. Pull a small set of daily/monthly aggregates from BigQuery (revenue by
   category, late-delivery rate, avg review score).
2. Flag rows where the latest value is > `Z_THRESHOLD` standard deviations
   from the trailing rolling mean (classic z-score check -- cheap, explainable,
   no ML infra required for a batch-daily pipeline this size).
3. Hand the flagged rows to Claude to turn into a short human-readable summary
   ("Electronics revenue fell 41% vs its 8-week average -- check for a stockout
   or pricing error"), rather than a raw table of numbers.
4. Post the summary to Slack (if SLACK_WEBHOOK_URL is set) and return it for
   the Airflow task log / XCom either way.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
import pandas as pd
from google.cloud import bigquery

Z_THRESHOLD = 2.0
LOOKBACK_PERIODS = 8

CHECKS = {
    "category_revenue": """
        SELECT
          product_category_name_english AS segment,
          DATE_TRUNC(order_purchase_date, WEEK) AS period,
          SUM(revenue) AS metric_value
        FROM `{project}.{gold_dataset}.fct_sales`
        WHERE order_purchase_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
        GROUP BY 1, 2
        ORDER BY 1, 2
    """,
    "late_delivery_rate": """
        SELECT
          customer_state AS segment,
          DATE_TRUNC(order_purchase_date, WEEK) AS period,
          AVG(CAST(is_late_delivery AS INT64)) AS metric_value
        FROM `{project}.{gold_dataset}.fct_delivery_performance`
        WHERE order_purchase_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
        GROUP BY 1, 2
        ORDER BY 1, 2
    """,
}


@dataclass
class Anomaly:
    check_name: str
    segment: str
    latest_value: float
    rolling_mean: float
    rolling_std: float
    z_score: float


def _zscore_flags(df: pd.DataFrame, check_name: str) -> list[Anomaly]:
    flags: list[Anomaly] = []
    for segment, g in df.groupby("segment"):
        g = g.sort_values("period")
        if len(g) < 4:
            continue
        history = g["metric_value"].iloc[-(LOOKBACK_PERIODS + 1):-1]
        latest = g["metric_value"].iloc[-1]
        mean, std = history.mean(), history.std(ddof=0)
        if std == 0 or np.isnan(std):
            continue
        z = (latest - mean) / std
        if abs(z) >= Z_THRESHOLD:
            flags.append(Anomaly(check_name, segment, latest, mean, std, z))
    return flags


def run_checks(project: str, gold_dataset: str) -> list[Anomaly]:
    client = bigquery.Client(project=project)
    all_flags: list[Anomaly] = []
    for check_name, sql in CHECKS.items():
        query = sql.format(project=project, gold_dataset=gold_dataset)
        df = client.query(query).to_dataframe()
        all_flags.extend(_zscore_flags(df, check_name))
    return all_flags


def narrate(flags: list[Anomaly]) -> str:
    """Turn the flagged rows into a short human-readable summary via Claude.
    Falls back to a plain templated summary if no API key is configured."""
    if not flags:
        return "No anomalies detected in today's gold-layer quality check."

    bullet_lines = "\n".join(
        f"- [{f.check_name}] segment={f.segment}: latest={f.latest_value:.3f}, "
        f"trailing_{LOOKBACK_PERIODS}wk_mean={f.rolling_mean:.3f}, z={f.z_score:.2f}"
        for f in flags
    )

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return f"Anomalies detected (LLM narration unavailable, raw flags below):\n{bullet_lines}"

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": (
                    "You are a data quality assistant for an e-commerce analytics "
                    "pipeline. Below are statistical anomalies (z-score >= "
                    f"{Z_THRESHOLD}) flagged in this run's gold-layer marts. Write a "
                    "concise, plain-English summary (max 6 bullet points) a business "
                    "stakeholder could read in Slack. Note direction (up/down), "
                    "rough magnitude, and one plausible business cause per item. "
                    "Do not invent numbers not given below.\n\n"
                    f"{bullet_lines}"
                ),
            }
        ],
    )
    return "".join(block.text for block in message.content if block.type == "text")


def post_to_slack(summary: str) -> None:
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        return
    import requests

    requests.post(webhook, json={"text": f"*Olist pipeline — daily quality check*\n{summary}"})


def run(project: str, gold_dataset: str) -> str:
    flags = run_checks(project, gold_dataset)
    summary = narrate(flags)
    post_to_slack(summary)
    return summary
