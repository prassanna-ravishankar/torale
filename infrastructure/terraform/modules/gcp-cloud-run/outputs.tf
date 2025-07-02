# Service URLs
output "frontend_url" {
  description = "URL of the frontend service"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "main_backend_url" {
  description = "URL of the main backend service"
  value       = google_cloud_run_v2_service.main_backend.uri
}

output "discovery_url" {
  description = "URL of the discovery service"
  value       = google_cloud_run_v2_service.discovery.uri
  sensitive   = true
}

output "monitoring_url" {
  description = "URL of the monitoring service"
  value       = google_cloud_run_v2_service.monitoring.uri
  sensitive   = true
}

output "notification_url" {
  description = "URL of the notification service"
  value       = google_cloud_run_v2_service.notification.uri
  sensitive   = true
}

# Service Names (for reference)
output "service_names" {
  description = "Map of service names"
  value = {
    frontend     = google_cloud_run_v2_service.frontend.name
    main_backend = google_cloud_run_v2_service.main_backend.name
    discovery    = google_cloud_run_v2_service.discovery.name
    monitoring   = google_cloud_run_v2_service.monitoring.name
    notification = google_cloud_run_v2_service.notification.name
  }
}

# Service Locations (for reference)
output "service_locations" {
  description = "Map of service locations"
  value = {
    frontend     = google_cloud_run_v2_service.frontend.location
    main_backend = google_cloud_run_v2_service.main_backend.location
    discovery    = google_cloud_run_v2_service.discovery.location
    monitoring   = google_cloud_run_v2_service.monitoring.location
    notification = google_cloud_run_v2_service.notification.location
  }
} 