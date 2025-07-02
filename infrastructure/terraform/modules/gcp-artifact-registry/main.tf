# Artifact Registry repository for Docker images
resource "google_artifact_registry_repository" "docker_repo" {
  repository_id = "${var.project_name}-docker"
  location      = var.location
  format        = "DOCKER"
  description   = "Docker repository for ${var.project_name} services"
  
  cleanup_policies {
    id     = "keep-recent-versions"
    action = "KEEP"
    
    most_recent_versions {
      keep_count = var.image_retention_count
    }
  }
  
  depends_on = [var.required_apis]
}

# IAM policy for Cloud Build to push images
resource "google_artifact_registry_repository_iam_member" "cloudbuild_push" {
  project    = var.project_id
  location   = google_artifact_registry_repository.docker_repo.location
  repository = google_artifact_registry_repository.docker_repo.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${var.cloudbuild_service_account_email}"
}

# IAM policies for service accounts to pull images
resource "google_artifact_registry_repository_iam_member" "service_accounts_pull" {
  for_each = var.service_account_emails
  
  project    = var.project_id
  location   = google_artifact_registry_repository.docker_repo.location
  repository = google_artifact_registry_repository.docker_repo.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${each.value}"
} 