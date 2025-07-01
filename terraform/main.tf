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
    "vpcaccess.googleapis.com",
    "compute.googleapis.com",
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

# VPC for internal communication
resource "google_compute_network" "vpc" {
  name                    = "${var.project_name}-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.required_apis]
}

# Subnet for VPC connector
resource "google_compute_subnetwork" "vpc_connector_subnet" {
  name          = "${var.project_name}-connector-subnet"
  network       = google_compute_network.vpc.name
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
}

# VPC Access Connector for Cloud Run internal communication
resource "google_vpc_access_connector" "connector" {
  name          = "${var.project_name}-connector"
  region        = var.region
  subnet {
    name = google_compute_subnetwork.vpc_connector_subnet.name
  }
  min_instances = 2
  max_instances = 10
  depends_on    = [google_project_service.required_apis]
}