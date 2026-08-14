resource "google_storage_bucket" "raw_data" {
  name     = var.gcs_bucket_name
  location = var.location
  project  = var.project

  storage_class               = var.storage_class
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action { type = "Delete" }
    condition { age = var.raw_data_retention_days }
  }

  force_destroy = var.force_destroy
}

output "bucket_name" {
  value = google_storage_bucket.raw_data.name
}

output "bucket_url" {
  value = "gs://${google_storage_bucket.raw_data.name}"
}
