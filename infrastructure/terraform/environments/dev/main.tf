terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.9"
    }
  }

  backend "gcs" {
    bucket  = "torale-464300-tf-state"
    prefix  = "environments/dev"
    credentials = "../../shared/terraform-credentials.json"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  credentials = "../../shared/terraform-credentials.json"
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com"
  ])
  
  service = each.value
  disable_on_destroy = false
}

# Wait for Cloud Build service account to be created
resource "time_sleep" "wait_for_cloudbuild_sa" {
  depends_on = [google_project_service.required_apis]
  create_duration = "60s"
}

# IAM Module
module "iam" {
  source = "../../modules/gcp-iam"
  
  project_id   = var.project_id
  project_name = var.project_name
  
  service_accounts = {
    frontend     = { display_name = "Frontend", description = "Service account for frontend application" }
    main-backend = { display_name = "Main Backend", description = "Service account for main backend API" }
    discovery    = { display_name = "Discovery", description = "Service account for discovery microservice" }
    monitoring   = { display_name = "Monitoring", description = "Service account for monitoring microservice" }
    notification = { display_name = "Notification", description = "Service account for notification microservice" }
  }
  
  cloudbuild_sa_dependency = time_sleep.wait_for_cloudbuild_sa
}

# Artifact Registry Module
module "artifact_registry" {
  source = "../../modules/gcp-artifact-registry"
  
  project_id                        = var.project_id
  project_name                      = var.project_name
  location                          = var.artifact_registry_location
  cloudbuild_service_account_email  = module.iam.cloudbuild_service_account_email
  service_account_emails            = module.iam.service_account_emails
  required_apis                     = [for api in google_project_service.required_apis : api.service]
}

# Cloud Run Module
module "cloud_run" {
  source = "../../modules/gcp-cloud-run"
  
  project_id                = var.project_id
  project_name              = var.project_name
  region                    = var.region
  artifact_registry_url     = module.artifact_registry.registry_url
  service_account_emails    = module.iam.service_account_emails
  
  # Environment variables
  database_url                      = var.database_url
  supabase_url                      = var.supabase_url
  supabase_anon_key                 = var.supabase_anon_key
  openai_api_key                    = var.openai_api_key
  perplexity_api_key                = var.perplexity_api_key
  notificationapi_client_id         = var.notificationapi_client_id
  notificationapi_client_secret     = var.notificationapi_client_secret
  
  # Scaling
  min_instances = var.min_instances
  max_instances = var.max_instances
  
  # Custom Domain Configuration
  enable_custom_domains = var.enable_cloudflare
  frontend_custom_domain = var.enable_cloudflare ? "app.${var.domain}" : ""
  backend_custom_domain = var.enable_cloudflare ? "api.${var.domain}" : ""
  
  required_apis = [for api in google_project_service.required_apis : api.service]
}

# Cloud Build Module
module "cloud_build" {
  source = "../../modules/gcp-cloud-build"
  
  project_id   = var.project_id
  project_name = var.project_name
  region       = var.region
  
  # GitHub configuration (disabled by default for dev)
  create_github_trigger = var.create_github_trigger
  github_owner         = var.github_owner
  github_repo          = var.github_repo
  
  # Registry URL from artifact registry module
  registry_url = module.artifact_registry.registry_url
  
  # Additional substitutions
  substitutions = {
    _SUPABASE_URL      = var.supabase_url
    _SUPABASE_ANON_KEY = var.supabase_anon_key
  }
}

# Cloudflare Module (optional)
module "cloudflare" {
  count  = var.enable_cloudflare ? 1 : 0
  source = "../../modules/cloudflare"
  
  domain              = var.domain
  project_name        = var.project_name
  frontend_target_url = var.enable_cloudflare ? "ghs.googlehosted.com" : module.cloud_run.frontend_url
  api_target_url      = var.enable_cloudflare ? "ghs.googlehosted.com" : module.cloud_run.main_backend_url
  
  # Disable advanced features that require higher API permissions
  enable_caching       = false
  enable_bot_protection = false
  
  # Disable proxy for Google Cloud Run domain mappings (required for SSL cert verification)
  enable_proxy = false
} 