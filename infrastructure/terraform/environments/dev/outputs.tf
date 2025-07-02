# IAM outputs
output "service_account_emails" {
  description = "Map of service account emails"
  value       = module.iam.service_account_emails
}

# Artifact Registry outputs
output "artifact_registry_url" {
  description = "URL of the Artifact Registry repository"
  value       = module.artifact_registry.registry_url
}

# Cloud Run outputs
output "frontend_url" {
  description = "URL of the frontend service"
  value       = module.cloud_run.frontend_url
}

output "main_backend_url" {
  description = "URL of the main backend service"
  value       = module.cloud_run.main_backend_url
}

output "discovery_service_url" {
  description = "URL of the discovery service"
  value       = module.cloud_run.discovery_url
  sensitive   = true
}

output "monitoring_service_url" {
  description = "URL of the monitoring service"
  value       = module.cloud_run.monitoring_url
  sensitive   = true
}

output "notification_service_url" {
  description = "URL of the notification service"
  value       = module.cloud_run.notification_url
  sensitive   = true
}

# Cloud Build outputs
output "cloud_build_trigger_created" {
  description = "Whether Cloud Build trigger was created"
  value       = module.cloud_build.trigger_created
}

# Cloudflare outputs (when enabled)
output "frontend_domain" {
  description = "Frontend domain name"
  value       = var.enable_cloudflare ? module.cloudflare[0].frontend_url : null
}

output "api_domain" {
  description = "API domain name"
  value       = var.enable_cloudflare ? module.cloudflare[0].api_url : null
}

output "region" {
  description = "GCP region where resources are deployed"
  value       = var.region
} 