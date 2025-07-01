output "frontend_url" {
  description = "URL of the frontend service"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "main_backend_url" {
  description = "URL of the main backend service (internal)"
  value       = google_cloud_run_v2_service.main_backend.uri
}

output "discovery_service_url" {
  description = "URL of the discovery service (internal)"
  value       = google_cloud_run_v2_service.discovery.uri
}

output "monitoring_service_url" {
  description = "URL of the content monitoring service (internal)"
  value       = google_cloud_run_v2_service.monitoring.uri
}

output "notification_service_url" {
  description = "URL of the notification service (internal)"
  value       = google_cloud_run_v2_service.notification.uri
}

output "artifact_registry_url" {
  description = "URL of the Artifact Registry repository"
  value       = "${var.artifact_registry_location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
}

output "region" {
  description = "GCP region where resources are deployed"
  value       = var.region
}