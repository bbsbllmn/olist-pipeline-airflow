terraform {
  required_version = ">= 1.7"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.24.0"
    }
  }
  backend "gcs" {}
}

provider "google" {
  project = var.project
  region  = var.region
}

module "storage" {
  source          = "../../modules/storage"
  project         = var.project
  location        = var.location
  gcs_bucket_name = var.gcs_bucket_name
  force_destroy   = true # dev only: allow terraform destroy to empty the bucket
}

module "bigquery" {
  source              = "../../modules/bigquery"
  project             = var.project
  location            = var.location
  bronze_dataset_name = var.bronze_dataset_name
  silver_dataset_name = var.silver_dataset_name
  gold_dataset_name   = var.gold_dataset_name
}

# No Composer in dev -- run Airflow via ../../../docker-compose.yml instead.
