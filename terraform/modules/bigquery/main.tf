resource "google_bigquery_dataset" "bronze" {
  dataset_id  = var.bronze_dataset_name
  project     = var.project
  location    = var.location
  description = "Bronze layer -- raw tables loaded 1:1 from GCS, no transformation."
}

resource "google_bigquery_dataset" "silver" {
  dataset_id  = var.silver_dataset_name
  project     = var.project
  location    = var.location
  description = "Silver layer -- dbt staging models: typed, deduplicated, renamed."
}

resource "google_bigquery_dataset" "gold" {
  dataset_id  = var.gold_dataset_name
  project     = var.project
  location    = var.location
  description = "Gold layer -- dbt marts: business-ready fact/dim tables for BI and AI."
}

output "bronze_dataset" {
  value = google_bigquery_dataset.bronze.dataset_id
}

output "silver_dataset" {
  value = google_bigquery_dataset.silver.dataset_id
}

output "gold_dataset" {
  value = google_bigquery_dataset.gold.dataset_id
}
