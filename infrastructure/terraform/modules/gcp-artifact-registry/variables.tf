variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "project_name" {
  description = "The project name (used for resource naming)"
  type        = string
}

variable "location" {
  description = "The location for the Artifact Registry repository"
  type        = string
  default     = "us-central1"
}

variable "image_retention_count" {
  description = "Number of recent image versions to keep"
  type        = number
  default     = 10
}

variable "cloudbuild_service_account_email" {
  description = "Email of the Cloud Build service account"
  type        = string
}

variable "service_account_emails" {
  description = "Map of service account emails that need pull access"
  type        = map(string)
  default     = {}
}

variable "required_apis" {
  description = "List of required APIs that must be enabled first"
  type        = list(string)
  default     = []
} 