# Project Configuration
variable "project_name" {
  description = "The name of the project (used as prefix for resources)"
  type        = string
}

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for Cloud Run services"
  type        = string
  default     = "us-central1"
}

# Service Account Configuration
variable "service_account_emails" {
  description = "Map of service account emails for each service"
  type = object({
    frontend     = string
    main-backend = string
    discovery    = string
    monitoring   = string
    notification = string
  })
}

# Docker Registry Configuration
variable "artifact_registry_url" {
  description = "Base URL for the Artifact Registry repository"
  type        = string
}

# Service Ports
variable "frontend_port" {
  description = "Port for the frontend service"
  type        = number
  default     = 3000
}

variable "backend_port" {
  description = "Port for the main backend service"
  type        = number
  default     = 8000
}

variable "discovery_port" {
  description = "Port for the discovery service"
  type        = number
  default     = 8001
}

variable "monitoring_port" {
  description = "Port for the monitoring service"
  type        = number
  default     = 8002
}

variable "notification_port" {
  description = "Port for the notification service"
  type        = number
  default     = 8003
}

# Scaling Configuration
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

# Resource Configuration
variable "frontend_resources" {
  description = "Resource limits for the frontend service"
  type = object({
    cpu    = string
    memory = string
  })
  default = {
    cpu    = "2"
    memory = "2Gi"
  }
}

variable "backend_resources" {
  description = "Resource limits for the main backend service"
  type = object({
    cpu    = string
    memory = string
  })
  default = {
    cpu    = "2"
    memory = "2Gi"
  }
}

variable "microservice_resources" {
  description = "Resource limits for microservices (discovery, monitoring, notification)"
  type = object({
    cpu    = string
    memory = string
  })
  default = {
    cpu    = "1"
    memory = "1Gi"
  }
}

# Database Configuration
variable "database_url" {
  description = "Database connection URL"
  type        = string
  sensitive   = true
}

# Supabase Configuration
variable "supabase_url" {
  description = "Supabase project URL"
  type        = string
}

variable "supabase_anon_key" {
  description = "Supabase anonymous key"
  type        = string
  sensitive   = true
}

# AI API Keys
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

# Notification API Configuration
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

# Dependencies
variable "required_apis" {
  description = "List of required GCP APIs that must be enabled"
  type        = list(any)
  default     = []
}

# Custom Domain Configuration
variable "enable_custom_domains" {
  description = "Whether to enable custom domain mappings for Cloud Run services"
  type        = bool
  default     = false
}

variable "frontend_custom_domain" {
  description = "Custom domain for the frontend service"
  type        = string
  default     = ""
}

variable "backend_custom_domain" {
  description = "Custom domain for the backend service"
  type        = string
  default     = ""
} 