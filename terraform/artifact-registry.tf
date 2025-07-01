# Artifact Registry repository for Docker images
resource "google_artifact_registry_repository" "docker_repo" {
  repository_id = "${var.project_name}-docker"
  location      = var.artifact_registry_location
  format        = "DOCKER"
  description   = "Docker repository for ${var.project_name} services"
  
  cleanup_policies {
    id     = "keep-recent-versions"
    action = "KEEP"
    
    most_recent_versions {
      keep_count = 10
    }
  }
  
  depends_on = [google_project_service.required_apis]
}