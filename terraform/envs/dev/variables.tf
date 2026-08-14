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
