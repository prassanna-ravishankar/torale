# Cloud Build trigger for automatic deployments
# Note: Requires GitHub App connection to be set up manually first
resource "google_cloudbuild_trigger" "deploy_trigger" {
  count       = var.create_github_trigger ? 1 : 0
  name        = "${var.project_name}-deploy"
  description = "Deploy all services on push to main branch"
  
  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = var.github_branch_pattern
    }
  }
  
  filename = var.cloudbuild_filename
  
  substitutions = merge(
    var.substitutions,
    {
      _PROJECT_ID   = var.project_id
      _REGION      = var.region
      _REGISTRY_URL = var.registry_url
    }
  )
} 