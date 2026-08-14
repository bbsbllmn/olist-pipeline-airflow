variable "project" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "location" {
  type    = string
  default = "US"
}

variable "gcs_bucket_name" {
  type = string
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

variable "composer_env_name" {
  type    = string
  default = "olist-airflow-prod"
}

variable "composer_service_account" {
  description = "Service account email for Composer's GKE nodes (needs roles/bigquery.dataEditor, roles/bigquery.jobUser, roles/storage.objectAdmin)"
  type        = string
}
