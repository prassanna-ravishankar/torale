# Data source to get project information
data "google_project" "project" {
  project_id = var.project_id
}

# Service accounts for each service
resource "google_service_account" "service_accounts" {
  for_each = var.service_accounts
  
  account_id   = "${var.project_name}-${each.key}"
  display_name = "Service account for ${var.project_name} ${each.value.display_name}"
  description  = each.value.description
}

# Grant Cloud Build service account necessary permissions
resource "google_project_iam_member" "cloudbuild_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
  
  depends_on = [var.cloudbuild_sa_dependency]
}

resource "google_project_iam_member" "cloudbuild_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
  
  depends_on = [var.cloudbuild_sa_dependency]
}

# Additional project-level IAM bindings
resource "google_project_iam_member" "additional_bindings" {
  for_each = var.additional_project_iam_bindings
  
  project = var.project_id
  role    = each.value.role
  member  = each.value.member
} 