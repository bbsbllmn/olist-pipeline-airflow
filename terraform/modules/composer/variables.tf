variable "project" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "composer_env_name" {
  type    = string
  default = "olist-airflow-prod"
}

variable "composer_image_version" {
  type    = string
  default = "composer-2.9.5-airflow-2.9.3"
}

variable "composer_service_account" {
  description = "Service account email Composer's GKE nodes run as (needs BigQuery + GCS + Secret Manager access)."
  type        = string
}

variable "bronze_dataset_name" {
  type    = string
  default = "olist_bronze"
}

variable "silver_dataset_name" {
  type    = string
  default = "olist_silver"
}

variable "gold_dataset_name" {
  type    = string
  default = "olist_gold"
}

variable "gcs_bucket_name" {
  type = string
}
