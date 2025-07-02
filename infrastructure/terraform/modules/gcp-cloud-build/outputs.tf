# Cloud Build Trigger Information
output "trigger_id" {
  description = "ID of the Cloud Build trigger (if created)"
  value       = var.create_github_trigger ? google_cloudbuild_trigger.deploy_trigger[0].id : null
}

output "trigger_name" {
  description = "Name of the Cloud Build trigger (if created)"
  value       = var.create_github_trigger ? google_cloudbuild_trigger.deploy_trigger[0].name : null
}

output "trigger_created" {
  description = "Whether the Cloud Build trigger was created"
  value       = var.create_github_trigger
} 