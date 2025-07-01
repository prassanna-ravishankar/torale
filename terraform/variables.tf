variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "torale"
}

variable "artifact_registry_location" {
  description = "Location for Artifact Registry"
  type        = string
  default     = "us-central1"
}

# Environment variables for services
variable "supabase_url" {
  description = "Supabase URL"
  type        = string
  sensitive   = true
}

variable "supabase_anon_key" {
  description = "Supabase anonymous key"
  type        = string
  sensitive   = true
}

variable "database_url" {
  description = "Database URL for backend services"
  type        = string
  sensitive   = true
}

variable "notificationapi_client_id" {
  description = "NotificationAPI Client ID"
  type        = string
  sensitive   = true
}

variable "notificationapi_client_secret" {
  description = "NotificationAPI Client Secret"
  type        = string
  sensitive   = true
}

variable "perplexity_api_key" {
  description = "Perplexity API Key"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
}

# Service configuration
variable "frontend_domain" {
  description = "Custom domain for frontend (optional)"
  type        = string
  default     = ""
}

variable "min_instances" {
  description = "Minimum number of instances for each service"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances for each service"
  type        = number
  default     = 100
}

# GitHub configuration for Cloud Build
variable "github_owner" {
  description = "GitHub repository owner"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}