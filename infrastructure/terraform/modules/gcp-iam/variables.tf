variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "project_name" {
  description = "The project name (used for resource naming)"
  type        = string
}

variable "service_accounts" {
  description = "Map of service accounts to create"
  type = map(object({
    display_name = string
    description  = string
  }))
  default = {}
}

variable "cloudbuild_sa_dependency" {
  description = "Dependency to ensure Cloud Build service account exists"
  type        = any
  default     = null
}

variable "additional_project_iam_bindings" {
  description = "Additional project-level IAM bindings"
  type = map(object({
    role   = string
    member = string
  }))
  default = {}
} 