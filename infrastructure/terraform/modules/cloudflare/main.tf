# Get the zone information
data "cloudflare_zone" "domain" {
  name = var.domain
}

# A record for frontend
resource "cloudflare_record" "frontend" {
  count = var.create_frontend_record ? 1 : 0
  
  zone_id         = data.cloudflare_zone.domain.id
  name            = var.frontend_subdomain
  content         = replace(var.frontend_target_url, "https://", "")
  type            = "CNAME"
  ttl             = var.enable_proxy ? 1 : var.dns_ttl
  proxied         = var.enable_proxy
  allow_overwrite = true
  
  comment = "Frontend service for ${var.project_name}"
}

# A record for API/backend
resource "cloudflare_record" "api" {
  count = var.create_api_record ? 1 : 0
  
  zone_id         = data.cloudflare_zone.domain.id
  name            = var.api_subdomain
  content         = replace(var.api_target_url, "https://", "")
  type            = "CNAME"
  ttl             = var.enable_proxy ? 1 : var.dns_ttl
  proxied         = var.enable_proxy
  allow_overwrite = true
  
  comment = "API service for ${var.project_name}"
}

# Additional DNS records
resource "cloudflare_record" "additional" {
  for_each = var.additional_records
  
  zone_id         = data.cloudflare_zone.domain.id
  name            = each.value.name
  content         = each.value.content
  type            = each.value.type
  ttl             = each.value.ttl
  proxied         = each.value.proxied
  allow_overwrite = true
  
  comment = each.value.comment
}

# Page rules for caching and security
resource "cloudflare_page_rule" "frontend_caching" {
  count = var.enable_caching ? 1 : 0
  
  zone_id  = data.cloudflare_zone.domain.id
  target   = "${var.frontend_subdomain}.${var.domain}/*"
  priority = 1

  actions {
    cache_level = "cache_everything"
    edge_cache_ttl = var.cache_ttl
    browser_cache_ttl = var.browser_cache_ttl
  }
}

# Firewall rules
resource "cloudflare_filter" "block_bad_bots" {
  count = var.enable_bot_protection ? 1 : 0
  
  zone_id     = data.cloudflare_zone.domain.id
  description = "Block known bad bots"
  expression  = "(cf.client.bot)"
}

resource "cloudflare_firewall_rule" "block_bad_bots" {
  count = var.enable_bot_protection ? 1 : 0
  
  zone_id     = data.cloudflare_zone.domain.id
  description = "Block known bad bots"
  filter_id   = cloudflare_filter.block_bad_bots[0].id
  action      = "block"
} 