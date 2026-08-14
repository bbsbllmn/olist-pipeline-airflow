"""
Thin Airflow operator wrapping include/dlt/kaggle_to_gcs_pipeline.run(), so the
DAG file stays declarative and the ingestion logic stays independently testable.
"""
from __future__ import annotations

from airflow.models import BaseOperator
from airflow.utils.context import Context


class DltKaggleToGCSOperator(BaseOperator):
    template_fields = ("gcs_bucket", "gcp_project_id")

    def __init__(self, gcs_bucket: str, gcp_project_id: str, **kwargs):
        super().__init__(**kwargs)
        self.gcs_bucket = gcs_bucket
        self.gcp_project_id = gcp_project_id

    def execute(self, context: Context):
        from include.dlt.kaggle_to_gcs_pipeline import run

        result = run(gcs_bucket=self.gcs_bucket, gcp_project_id=self.gcp_project_id)
        self.log.info("dlt load complete: %s", result)
        return result
