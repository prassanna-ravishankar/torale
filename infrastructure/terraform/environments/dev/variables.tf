# Project configuration
variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "project_name" {
  description = "The project name (used for resource naming)"
  type        = string
  default     = "torale"
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "artifact_registry_location" {
  description = "Location for the Artifact Registry"
  type        = string
  default     = "us-central1"
}

# Environment variables for services
variable "database_url" {
  description = "Database connection URL"
  type        = string
  sensitive   = true
}

variable "supabase_url" {
  description = "Supabase project URL"
  type        = string
  sensitive   = true
}

variable "supabase_anon_key" {
  description = "Supabase anonymous key"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "perplexity_api_key" {
  description = "Perplexity API key"
  type        = string
  sensitive   = true
}

variable "notificationapi_client_id" {
  description = "NotificationAPI client ID"
  type        = string
  sensitive   = true
}

variable "notificationapi_client_secret" {
  description = "NotificationAPI client secret"
  type        = string
  sensitive   = true
}

# Cloud Run scaling
variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 100
}

# GitHub configuration for Cloud Build
variable "create_github_trigger" {
  description = "Whether to create GitHub trigger for Cloud Build"
  type        = bool
  default     = false
}

variable "github_owner" {
  description = "GitHub organization or username"
  type        = string
  default     = ""
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = ""
}

# Cloudflare configuration (optional)
variable "enable_cloudflare" {
  description = "Whether to enable Cloudflare DNS management"
  type        = bool
  default     = false
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "domain" {
  description = "Domain name for Cloudflare management"
  type        = string
  default     = ""
} 