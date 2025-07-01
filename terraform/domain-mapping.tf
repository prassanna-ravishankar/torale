# Domain mapping for frontend service
resource "google_cloud_run_domain_mapping" "frontend_domain" {
  count    = var.frontend_domain != "" ? 1 : 0
  name     = var.frontend_domain
  location = google_cloud_run_v2_service.frontend.location
  
  spec {
    route_name = google_cloud_run_v2_service.frontend.name
  }
  
  metadata {
    namespace = var.project_id
    annotations = {
      "run.googleapis.com/launch-stage" = "GA"
    }
  }
  
  depends_on = [google_cloud_run_v2_service.frontend]
}

# Output the DNS records needed for Cloudflare
output "cloudflare_dns_records" {
  description = "DNS records to add in Cloudflare"
  value = var.frontend_domain != "" ? {
    instructions = "Add these DNS records in Cloudflare:"
    records = [
      {
        type  = "CNAME"
        name  = var.frontend_domain == "torale.ai" ? "@" : replace(var.frontend_domain, ".torale.ai", "")
        value = "ghs.googlehosted.com"
        proxy = false
        ttl   = 3600
        note  = "Set Proxy status to DNS only (gray cloud)"
      }
    ]
    important_notes = [
      "1. The proxy must be DISABLED (gray cloud) for Cloud Run to work",
      "2. It may take up to 24 hours for the domain to be fully verified",
      "3. You can check status with: gcloud run domain-mappings list --region=${var.region}"
    ]
  } : null
}