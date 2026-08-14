output "gcs_bucket_url" {
  value = module.storage.bucket_url
}

output "bronze_dataset" {
  value = module.bigquery.bronze_dataset
}

output "silver_dataset" {
  value = module.bigquery.silver_dataset
}

output "gold_dataset" {
  value = module.bigquery.gold_dataset
}

output "composer_dag_bucket" {
  value       = module.composer.composer_dag_bucket
  description = "GCS path Composer watches for DAGs -- sync ./dags and ./include here."
}

output "airflow_uri" {
  value = module.composer.airflow_uri
}
