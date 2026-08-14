resource "google_composer_environment" "olist_airflow" {
  name    = var.composer_env_name
  project = var.project
  region  = var.region

  config {
    software_config {
      image_version = var.composer_image_version

      pypi_packages = {
        dbt-core      = "==1.8.7"
        dbt-bigquery  = "==1.8.3"
        dlt           = "[bigquery,filesystem]==1.4.1"
        anthropic     = "==0.34.2"
        kaggle        = "==1.6.17"
      }

      env_variables = {
        GCP_PROJECT_ID    = var.project
        BQ_BRONZE_DATASET = var.bronze_dataset_name
        BQ_SILVER_DATASET = var.silver_dataset_name
        BQ_GOLD_DATASET   = var.gold_dataset_name
        GCS_BUCKET        = var.gcs_bucket_name
      }
    }

    workloads_config {
      scheduler {
        cpu        = 1
        memory_gb  = 2
        storage_gb = 1
        count      = 1
      }
      web_server {
        cpu        = 0.5
        memory_gb  = 2
        storage_gb = 1
      }
      worker {
        cpu        = 1
        memory_gb  = 4
        storage_gb = 5
        min_count  = 1
        max_count  = 3
      }
    }

    environment_size = "ENVIRONMENT_SIZE_SMALL"

    node_config {
      service_account = var.composer_service_account
    }
  }
}

output "composer_dag_bucket" {
  description = "GCS bucket Composer watches for DAGs -- sync ./dags and ./include here."
  value       = google_composer_environment.olist_airflow.config[0].dag_gcs_prefix
}

output "airflow_uri" {
  value = google_composer_environment.olist_airflow.config[0].airflow_uri
}
