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
  description = "The GCP region"
  type        = string
}

# GitHub Configuration
variable "create_github_trigger" {
  description = "Whether to create the GitHub trigger"
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

variable "github_branch_pattern" {
  description = "Git branch pattern to trigger builds"
  type        = string
  default     = "^main$"
}

# Build Configuration
variable "cloudbuild_filename" {
  description = "Path to the Cloud Build configuration file"
  type        = string
  default     = "cloudbuild.yaml"
}

variable "registry_url" {
  description = "Docker registry URL for storing images"
  type        = string
}

# Substitutions
variable "substitutions" {
  description = "Additional substitutions for Cloud Build"
  type        = map(string)
  default     = {}
}

 