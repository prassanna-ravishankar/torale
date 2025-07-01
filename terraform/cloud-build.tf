# Cloud Build trigger for automatic deployments
resource "google_cloudbuild_trigger" "deploy_trigger" {
  name        = "${var.project_name}-deploy"
  description = "Deploy all services on push to main branch"
  
  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = "^main$"
    }
  }
  
  filename = "cloudbuild.yaml"
  
  substitutions = {
    _PROJECT_ID    = var.project_id
    _REGION        = var.region
    _REGISTRY_URL  = "${var.artifact_registry_location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_artifact_registry_repository.docker_repo
  ]
}