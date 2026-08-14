"""
Small FastAPI service that lets a stakeholder ask a plain-English question
about the gold marts and get back a SQL query + its result, run read-only
against BigQuery. Runs as its own container in docker-compose
(`ai-nl2sql-api`), independent of the Airflow scheduler.

Design choices:
- Only queries `marts.yml`-documented gold tables (schema is injected into the
  prompt from BigQuery's INFORMATION_SCHEMA, not hardcoded, so it stays correct
  as dbt models evolve).
- The generated SQL is always shown back to the caller for auditability before
  it's clear whether they trust it -- this is a transparency tool, not an
  autonomous agent.
- Query is executed with `dry_run` cost estimation first and a hard row-limit,
  since this sits behind a chat-style endpoint that non-engineers will use.
"""
from __future__ import annotations

import os

import anthropic
from fastapi import FastAPI, HTTPException
from google.cloud import bigquery
from pydantic import BaseModel

app = FastAPI(title="Olist Marts NL-to-SQL")

PROJECT = os.environ.get("GCP_PROJECT_ID", "")
GOLD_DATASET = os.environ.get("BQ_GOLD_DATASET", "olist_gold")
MAX_ROWS = 500


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    sql: str
    rows: list[dict]
    row_count: int


def _get_gold_schema(client: bigquery.Client) -> str:
    query = f"""
        SELECT table_name, column_name, data_type
        FROM `{PROJECT}.{GOLD_DATASET}.INFORMATION_SCHEMA.COLUMNS`
        ORDER BY table_name, ordinal_position
    """
    rows = client.query(query).result()
    schema: dict[str, list[str]] = {}
    for r in rows:
        schema.setdefault(r.table_name, []).append(f"{r.column_name} ({r.data_type})")
    return "\n".join(f"{t}: {', '.join(cols)}" for t, cols in schema.items())


def _generate_sql(question: str, schema: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[
            {
                "role": "user",
                "content": (
                    "You write BigQuery Standard SQL against the schema below. "
                    "Return ONLY the SQL query, no explanation, no markdown fences. "
                    f"Always fully-qualify tables as `{PROJECT}.{GOLD_DATASET}.<table>` "
                    f"and always include a `LIMIT {MAX_ROWS}` clause. Only SELECT "
                    "statements are allowed -- never write DML/DDL.\n\n"
                    f"Schema:\n{schema}\n\n"
                    f"Question: {question}"
                ),
            }
        ],
    )
    sql = "".join(b.text for b in message.content if b.type == "text").strip()
    if not sql.lstrip().upper().startswith("SELECT"):
        raise HTTPException(400, "Generated query was not a SELECT statement; refused.")
    return sql


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    client = bigquery.Client(project=PROJECT)
    schema = _get_gold_schema(client)
    sql = _generate_sql(req.question, schema)

    job_config = bigquery.QueryJobConfig(dry_run=True)
    client.query(sql, job_config=job_config)  # validates + estimates cost, raises on bad SQL

    result = client.query(sql).result(max_results=MAX_ROWS)
    rows = [dict(row) for row in result]
    return AskResponse(sql=sql, rows=rows, row_count=len(rows))


@app.get("/health")
def health():
    return {"status": "ok"}
