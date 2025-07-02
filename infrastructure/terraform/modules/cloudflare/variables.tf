variable "domain" {
  description = "The domain name to manage in Cloudflare"
  type        = string
}

variable "project_name" {
  description = "The project name (used for comments and naming)"
  type        = string
}

# Frontend configuration
variable "create_frontend_record" {
  description = "Whether to create a DNS record for the frontend"
  type        = bool
  default     = true
}

variable "frontend_subdomain" {
  description = "Subdomain for the frontend (e.g., 'www' or 'app')"
  type        = string
  default     = "app"
}

variable "frontend_target_url" {
  description = "Target URL for the frontend DNS record"
  type        = string
}

# API configuration
variable "create_api_record" {
  description = "Whether to create a DNS record for the API"
  type        = bool
  default     = true
}

variable "api_subdomain" {
  description = "Subdomain for the API (e.g., 'api')"
  type        = string
  default     = "api"
}

variable "api_target_url" {
  description = "Target URL for the API DNS record"
  type        = string
}

# DNS settings
variable "dns_ttl" {
  description = "TTL for DNS records"
  type        = number
  default     = 300
}

variable "enable_proxy" {
  description = "Whether to enable Cloudflare proxy (orange cloud)"
  type        = bool
  default     = true
}

# Additional records
variable "additional_records" {
  description = "Additional DNS records to create"
  type = map(object({
    name    = string
    content = string
    type    = string
    ttl     = number
    proxied = bool
    comment = string
  }))
  default = {}
}

# Caching configuration
variable "enable_caching" {
  description = "Whether to enable caching rules"
  type        = bool
  default     = true
}

variable "cache_ttl" {
  description = "Edge cache TTL in seconds"
  type        = number
  default     = 86400  # 24 hours
}

variable "browser_cache_ttl" {
  description = "Browser cache TTL in seconds"
  type        = number
  default     = 14400  # 4 hours
}

# Security configuration
variable "enable_bot_protection" {
  description = "Whether to enable bot protection rules"
  type        = bool
  default     = true
} 