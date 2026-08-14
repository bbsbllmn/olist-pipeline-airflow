# Olist E-Commerce Analytics Pipeline — Airflow + dbt + GCP + AI

End-to-end batch data pipeline for the Olist Brazilian e-commerce dataset, rebuilt from the
[original Kestra version](https://github.com/abbasbill/Olist-ecommerce-pipeline-analytics)
on **Apache Airflow**, with an AI-driven quality, documentation, and analytics-chat layer.

## 1. Architecture

```
Kaggle CSV ──dlt──▶ GCS (raw/bronze)  ──BQ load──▶  BigQuery bronze dataset
                                                          │
                                                          ▼
                                        dbt staging (silver) ── cleaned, typed, deduped
                                                          │
                                                          ▼
                                        dbt marts (gold) ── business-ready fact/dim tables
                                                          │
                              ┌───────────────────────────┼──────────────────────────┐
                              ▼                            ▼                          ▼
                     Looker Studio dashboards     AI anomaly detection        AI NL→SQL chat
                     (revenue, delivery, RFM)      (posts to Slack/email)      (ask the marts)
```

**Orchestration:** Apache Airflow. `docker-compose.yml` runs a full local stack
(LocalExecutor + Postgres) for development; `terraform/modules/composer` provisions
**Cloud Composer 2** for production, so the *same DAG code* runs in both environments —
only the `GCP_ENV` variable and Airflow Variables/Connections change.

**Medallion layers (BigQuery datasets):**
| Layer | Dataset | Contents |
|---|---|---|
| Bronze | `olist_bronze` | Raw CSV loaded 1:1 from GCS, no transformation |
| Silver | `olist_silver` (dbt `staging`) | Typed, deduplicated, renamed columns |
| Gold | `olist_gold` (dbt `marts`) | Fact tables, RFM customer segments, seller scorecards |

## 2. Why this rebuild adds business value over the original

The original project stopped at a single `fct_sales` fact table. This version adds:

- **`dim_customers_rfm`** — Recency/Frequency/Monetary segmentation → identifies at-risk
  high-value customers and campaign targets, refreshed every run.
- **`fct_delivery_performance`** — actual vs. estimated delivery date, late-delivery flag,
  carrier lead time by state → operational lever for logistics negotiation.
- **`dim_sellers_performance`** — seller-level revenue, review score, late-delivery rate,
  cancellation rate → seller scorecarding / marketplace curation.
- **`mart_monthly_revenue`** — revenue, freight, AOV, YoY/MoM growth, pre-aggregated for BI.
- **AI anomaly detection** — statistical (z-score/IQR) + LLM-narrated daily check on the
  gold marts, flags e.g. a category's revenue dropping >2σ and explains *why* in plain
  English before a human opens the dashboard.
- **AI NL→SQL chat** — a small FastAPI service so non-technical stakeholders can ask
  "which product category had the most late deliveries last month?" directly against
  the gold marts, with the generated SQL shown for auditability.
- **AI doc summarizer** — turns dbt's machine-readable `manifest.json` into a
  plain-English changelog posted after every `dbt build`, so the docs stay current
  without manual upkeep.

## 3. Repo layout

```
.
├── dags/                    # Airflow DAGs (5), portable across Compose & Composer
├── plugins/operators/       # Custom Airflow operators (dlt wrapper)
├── include/
│   ├── dlt/                 # dlt pipeline: Kaggle → GCS
│   └── ai/                  # anomaly detection, NL→SQL, doc summarizer
├── dbt/olist_analytics/     # dbt project (staging + intermediate + marts)
├── terraform/
│   ├── modules/{storage,bigquery,composer}
│   └── envs/{dev,prod}      # thin wrappers that call the modules
├── docker-compose.yml       # local Airflow stack
├── Dockerfile                # Airflow image with dbt + dlt + AI deps baked in
└── scripts/encode-secret.sh
```

## 4. Quickstart (local dev)

```bash
cp .env.example .env                 # fill in GCP_PROJECT_ID, GCS bucket, API keys
mv ~/Downloads/gcp-credentials.json ./keys/gcp-credentials.json

docker compose up -d --build
# Airflow UI → http://localhost:8080  (user: airflow / pass: airflow)
```

Unpause `olist_ingestion_dag` — it triggers the rest of the DAG chain via
`TriggerDagRunOperator` / dataset-aware scheduling (`Dataset("bq://olist_bronze")`, etc.).

## 5. Provisioning GCP with Terraform

`terraform/envs/dev` and `terraform/envs/prod` are independent Terraform roots (each
with its own backend/provider block — Terraform doesn't allow backend blocks in shared
modules) that both call the same `terraform/modules/{storage,bigquery,composer}`.

**Dev** — just the GCS bucket + 3 BigQuery datasets (bronze/silver/gold); Airflow itself
runs locally via `docker-compose.yml`:
```bash
cd terraform/envs/dev
cp terraform.tfvars.example terraform.tfvars   # fill in project id, bucket name
terraform init -backend-config="bucket=<your-tf-state-bucket>" -backend-config="prefix=dev"
terraform apply
```

**Prod** — same, plus a Cloud Composer 2 (managed Airflow) environment:
```bash
cd terraform/envs/prod
cp terraform.tfvars.example terraform.tfvars   # fill in project id, bucket name, service account
terraform init -backend-config="bucket=<your-tf-state-bucket>" -backend-config="prefix=prod"
terraform apply

terraform output composer_dag_bucket   # GCS path Composer watches for DAGs
gsutil -m rsync -r ../../../dags gs://<composer-dag-bucket>/dags
gsutil -m rsync -r ../../../include gs://<composer-dag-bucket>/data/include
```

Composer picks up the same DAG files unchanged — they read GCP config from Airflow
Variables (`Variable.get("gcp_project_id")`, set once via `airflow variables set` or the
UI) instead of `.env`, so the DAG code path is identical in both environments.

## 6. DAG chain

1. `olist_ingestion_dag` — dlt pulls the Kaggle CSVs, lands them in `gs://<bucket>/raw/`.
2. `olist_bq_load_dag` — loads GCS → `olist_bronze.*` native BQ tables (triggered by GCS
   object creation via dataset scheduling).
3. `olist_dbt_transform_dag` — runs `dbt build` (staging + marts), publishes docs.
4. `olist_ai_quality_dag` — runs anomaly detection over the gold marts, posts findings.
5. `olist_docs_dag` — summarizes the latest `dbt build` diff with an LLM, posts changelog.

See each module's docstring for details.
