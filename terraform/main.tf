terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}
provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_storage_bucket" "data" {
  name                        = var.bucket_name
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
}

output "bucket_url" {
  value = google_storage_bucket.data.url
}
