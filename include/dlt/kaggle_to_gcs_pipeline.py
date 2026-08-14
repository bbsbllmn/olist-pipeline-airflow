"""
Downloads the Kaggle Olist Brazilian E-Commerce dataset and lands each CSV as
Parquet in GCS under gs://<bucket>/raw/<table>/, partitioned by load date.

Used by dags/olist_ingestion_dag.py via the DltRunOperator. Kept as a plain
importable function (rather than a notebook/script) so it's unit-testable and
so the DAG only needs to import + call it.
"""
from __future__ import annotations

import os
from pathlib import Path

import dlt
import pandas as pd
import kagglehub

KAGGLE_DATASET = "olistbr/brazilian-ecommerce"

# source CSV filename -> destination bronze table name
TABLE_MAP = {
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_products_dataset.csv": "products",
    "olist_customers_dataset.csv": "customers",
    "olist_sellers_dataset.csv": "sellers",
    "olist_geolocation_dataset.csv": "geolocation",
    "product_category_name_translation.csv": "product_category_translation",
}

def _download_kaggle_dataset(download_dir: Path) -> Path:
    """Requires KAGGLE_USERNAME / KAGGLE_KEY env vars (set by Airflow Connection
    or .env). Returns the directory containing the extracted CSVs."""
    path = kagglehub.dataset_download(
        KAGGLE_DATASET,
        force_download=False,  # match old force=True: always re-fetch, don't trust stale cache
    )
    csv_dir = Path(path)

    # kagglehub may nest files under a subfolder of output_dir rather than
    # dropping them flat -- locate the actual CSVs instead of assuming layout.
    if not any((csv_dir / name).exists() for name in TABLE_MAP):
        found = next(csv_dir.rglob("olist_orders_dataset.csv"), None)
        if found is None:
            raise RuntimeError(f"Could not locate extracted CSVs under {csv_dir}")
        csv_dir = found.parent

    return csv_dir
        
@dlt.source
def olist_source(csv_dir: Path):
    """One dlt resource per raw CSV, yielded as pandas records so dlt can infer
    schema and handle typing/normalization before landing in GCS."""

    def _make_resource(csv_name: str, table_name: str):
        @dlt.resource(name=table_name, write_disposition="replace")
        def resource():
            df = pd.read_csv(csv_dir / csv_name)
            yield df.to_dict(orient="records")

        return resource

    for csv_name, table_name in TABLE_MAP.items():
        if (csv_dir / csv_name).exists():
            yield _make_resource(csv_name, table_name)()


def run(gcs_bucket: str, gcp_project_id: str) -> dict:
    """Entry point called by the Airflow operator. Returns a summary dict
    (row counts per table) that gets pushed to XCom."""
    work_dir = Path("/tmp/olist_kaggle_raw")
    csv_dir = _download_kaggle_dataset(work_dir)

    pipeline = dlt.pipeline(
        pipeline_name="olist_kaggle_to_gcs",
        destination=dlt.destinations.filesystem(
            bucket_url=f"gs://{gcs_bucket}/raw",
            layout="{table_name}/{load_id}.{file_id}.{ext}",
        ),
        dataset_name="olist_raw",
    )

    load_info = pipeline.run(
        olist_source(csv_dir),
        loader_file_format="parquet",
    )

    summary = {}
    for pkg in load_info.load_packages:
        for job in pkg.jobs.get("completed_jobs", []):
            summary[job.job_file_info.table_name] = summary.get(
                job.job_file_info.table_name, 0
            ) + 1

    return {"tables_loaded": list(TABLE_MAP.values()), "load_id": load_info.loads_ids}
