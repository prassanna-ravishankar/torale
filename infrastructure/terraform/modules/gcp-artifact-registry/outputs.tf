output "registry_url" {
  description = "The full URL of the Artifact Registry repository"
  value       = "${var.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
}

output "repository_id" {
  description = "The ID of the Artifact Registry repository"
  value       = google_artifact_registry_repository.docker_repo.repository_id
}

output "repository_name" {
  description = "The name of the Artifact Registry repository"
  value       = google_artifact_registry_repository.docker_repo.name
}

output "location" {
  description = "The location of the Artifact Registry repository"
  value       = google_artifact_registry_repository.docker_repo.location
} 