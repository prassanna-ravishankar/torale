terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.9"
    }
  }

  backend "gcs" {
    bucket  = "torale-464300-tf-state"
    prefix  = "terraform/state"
    credentials = "./terraform-credentials.json"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com"
  ])
  
  service = each.value
  disable_on_destroy = false
}

# Wait for Cloud Build service account to be created
resource "time_sleep" "wait_for_cloudbuild_sa" {
  depends_on = [google_project_service.required_apis]
  create_duration = "60s"
}