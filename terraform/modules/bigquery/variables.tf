variable "project" {
  type = string
}

variable "location" {
  type    = string
  default = "US"
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
