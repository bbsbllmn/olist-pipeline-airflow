variable "project" {
  type = string
}

variable "location" {
  type    = string
  default = "US"
}

variable "gcs_bucket_name" {
  type = string
}

variable "storage_class" {
  type    = string
  default = "STANDARD"
}

variable "raw_data_retention_days" {
  type    = number
  default = 90
}

variable "force_destroy" {
  type    = bool
  default = false
}
