terraform {
  required_version = ">= 1.7"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.24.0"
    }
  }
  backend "gcs" {
    # terraform init -backend-config="bucket=olist-terraform-state" -backend-config="prefix=prod"
  }
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
  force_destroy   = false # prod: never auto-delete raw data on destroy
}

module "bigquery" {
  source              = "../../modules/bigquery"
  project             = var.project
  location            = var.location
  bronze_dataset_name = var.bronze_dataset_name
  silver_dataset_name = var.silver_dataset_name
  gold_dataset_name   = var.gold_dataset_name
}

module "composer" {
  source                   = "../../modules/composer"
  project                  = var.project
  region                   = var.region
  composer_env_name        = var.composer_env_name
  composer_service_account = var.composer_service_account
  bronze_dataset_name      = var.bronze_dataset_name
  silver_dataset_name      = var.silver_dataset_name
  gold_dataset_name        = var.gold_dataset_name
  gcs_bucket_name          = module.storage.bucket_name
}
