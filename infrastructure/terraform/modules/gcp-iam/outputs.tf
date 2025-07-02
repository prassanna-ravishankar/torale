output "service_account_emails" {
  description = "Map of service account emails"
  value       = { for k, v in google_service_account.service_accounts : k => v.email }
}

output "service_account_ids" {
  description = "Map of service account IDs"
  value       = { for k, v in google_service_account.service_accounts : k => v.id }
}

output "cloudbuild_service_account_email" {
  description = "Email of the Cloud Build service account"
  value       = "${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

output "project_number" {
  description = "The GCP project number"
  value       = data.google_project.project.number
} 