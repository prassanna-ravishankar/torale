output "zone_id" {
  description = "The Cloudflare zone ID"
  value       = data.cloudflare_zone.domain.id
}

output "frontend_url" {
  description = "The frontend URL"
  value       = var.create_frontend_record ? "${var.frontend_subdomain}.${var.domain}" : null
}

output "api_url" {
  description = "The API URL"
  value       = var.create_api_record ? "${var.api_subdomain}.${var.domain}" : null
}

output "frontend_record_id" {
  description = "The ID of the frontend DNS record"
  value       = var.create_frontend_record ? cloudflare_record.frontend[0].id : null
}

output "api_record_id" {
  description = "The ID of the API DNS record"
  value       = var.create_api_record ? cloudflare_record.api[0].id : null
}

output "additional_record_ids" {
  description = "Map of additional DNS record IDs"
  value       = { for k, v in cloudflare_record.additional : k => v.id }
} 