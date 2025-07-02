# Frontend Service (Public)
resource "google_cloud_run_v2_service" "frontend" {
  name     = "${var.project_name}-frontend"
  location = var.region
  
  template {
    service_account = var.service_account_emails.frontend
    
    containers {
      image = "${var.artifact_registry_url}/frontend:latest"
      
      ports {
        container_port = var.frontend_port
      }
      
      env {
        name  = "NEXT_PUBLIC_SUPABASE_URL"
        value = var.supabase_url
      }
      
      env {
        name  = "NEXT_PUBLIC_SUPABASE_ANON_KEY"
        value = var.supabase_anon_key
      }
      
      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = google_cloud_run_v2_service.main_backend.uri
      }
      
      resources {
        limits = {
          cpu    = var.frontend_resources.cpu
          memory = var.frontend_resources.memory
        }
      }
    }
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  
  depends_on = [var.required_apis]
}

# Main Backend Service (Public)
resource "google_cloud_run_v2_service" "main_backend" {
  name     = "${var.project_name}-main-backend"
  location = var.region
  
  template {
    service_account = var.service_account_emails["main-backend"]
    
    containers {
      image = "${var.artifact_registry_url}/backend:latest"
      
      ports {
        container_port = var.backend_port
      }
      
      env {
        name  = "DATABASE_URL"
        value = var.database_url
      }
      
      env {
        name  = "SUPABASE_URL"
        value = var.supabase_url
      }
      
      env {
        name  = "SUPABASE_SERVICE_KEY"
        value = var.supabase_anon_key
      }
      
      env {
        name  = "DISCOVERY_SERVICE_URL"
        value = google_cloud_run_v2_service.discovery.uri
      }
      
      env {
        name  = "MONITORING_SERVICE_URL"
        value = google_cloud_run_v2_service.monitoring.uri
      }
      
      env {
        name  = "NOTIFICATION_SERVICE_URL"
        value = google_cloud_run_v2_service.notification.uri
      }
      
      resources {
        limits = {
          cpu    = var.backend_resources.cpu
          memory = var.backend_resources.memory
        }
      }
    }
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  
  ingress = "INGRESS_TRAFFIC_ALL"
  
  depends_on = [var.required_apis]
}

# Discovery Service (IAM-protected)
resource "google_cloud_run_v2_service" "discovery" {
  name     = "${var.project_name}-discovery"
  location = var.region
  
  template {
    service_account = var.service_account_emails.discovery
    
    containers {
      image = "${var.artifact_registry_url}/discovery-service:latest"
      
      ports {
        container_port = var.discovery_port
      }
      
      env {
        name  = "DATABASE_URL"
        value = var.database_url
      }
      
      env {
        name  = "SUPABASE_URL"
        value = var.supabase_url
      }
      
      env {
        name  = "SUPABASE_SERVICE_KEY"
        value = var.supabase_anon_key
      }
      
      env {
        name  = "PERPLEXITY_API_KEY"
        value = var.perplexity_api_key
      }
      
      env {
        name  = "OPENAI_API_KEY"
        value = var.openai_api_key
      }
      
      resources {
        limits = {
          cpu    = var.microservice_resources.cpu
          memory = var.microservice_resources.memory
        }
      }
    }
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  
  ingress = "INGRESS_TRAFFIC_ALL"
  
  depends_on = [var.required_apis]
}

# Content Monitoring Service (IAM-protected)
resource "google_cloud_run_v2_service" "monitoring" {
  name     = "${var.project_name}-monitoring"
  location = var.region
  
  template {
    service_account = var.service_account_emails.monitoring
    
    containers {
      image = "${var.artifact_registry_url}/content-monitoring-service:latest"
      
      ports {
        container_port = var.monitoring_port
      }
      
      env {
        name  = "DATABASE_URL"
        value = var.database_url
      }
      
      env {
        name  = "SUPABASE_URL"
        value = var.supabase_url
      }
      
      env {
        name  = "SUPABASE_SERVICE_KEY"
        value = var.supabase_anon_key
      }
      
      env {
        name  = "OPENAI_API_KEY"
        value = var.openai_api_key
      }
      
      resources {
        limits = {
          cpu    = var.microservice_resources.cpu
          memory = var.microservice_resources.memory
        }
      }
    }
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  
  ingress = "INGRESS_TRAFFIC_ALL"
  
  depends_on = [var.required_apis]
}

# Notification Service (IAM-protected)
resource "google_cloud_run_v2_service" "notification" {
  name     = "${var.project_name}-notification"
  location = var.region
  
  template {
    service_account = var.service_account_emails.notification
    
    containers {
      image = "${var.artifact_registry_url}/notification-service:latest"
      
      ports {
        container_port = var.notification_port
      }
      
      env {
        name  = "DATABASE_URL"
        value = var.database_url
      }
      
      env {
        name  = "SUPABASE_URL"
        value = var.supabase_url
      }
      
      env {
        name  = "SUPABASE_SERVICE_KEY"
        value = var.supabase_anon_key
      }
      
      env {
        name  = "NOTIFICATIONAPI_CLIENT_ID"
        value = var.notificationapi_client_id
      }
      
      env {
        name  = "NOTIFICATIONAPI_CLIENT_SECRET"
        value = var.notificationapi_client_secret
      }
      
      resources {
        limits = {
          cpu    = var.microservice_resources.cpu
          memory = var.microservice_resources.memory
        }
      }
    }
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  
  ingress = "INGRESS_TRAFFIC_ALL"
  
  depends_on = [var.required_apis]
}

# IAM: Make frontend service publicly accessible
resource "google_cloud_run_service_iam_member" "frontend_public" {
  service  = google_cloud_run_v2_service.frontend.name
  location = google_cloud_run_v2_service.frontend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# IAM: Make main backend service publicly accessible
resource "google_cloud_run_service_iam_member" "main_backend_public" {
  service  = google_cloud_run_v2_service.main_backend.name
  location = google_cloud_run_v2_service.main_backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# IAM: Allow frontend to invoke main backend
resource "google_cloud_run_service_iam_member" "frontend_invoke_main_backend" {
  service  = google_cloud_run_v2_service.main_backend.name
  location = google_cloud_run_v2_service.main_backend.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.service_account_emails.frontend}"
}

# IAM: Allow main backend to invoke microservices
resource "google_cloud_run_service_iam_member" "discovery_backend_access" {
  service  = google_cloud_run_v2_service.discovery.name
  location = google_cloud_run_v2_service.discovery.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.service_account_emails["main-backend"]}"
}

resource "google_cloud_run_service_iam_member" "monitoring_backend_access" {
  service  = google_cloud_run_v2_service.monitoring.name
  location = google_cloud_run_v2_service.monitoring.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.service_account_emails["main-backend"]}"
}

resource "google_cloud_run_service_iam_member" "notification_backend_access" {
  service  = google_cloud_run_v2_service.notification.name
  location = google_cloud_run_v2_service.notification.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.service_account_emails["main-backend"]}"
}

# Domain Mappings for Custom Domains
resource "google_cloud_run_domain_mapping" "frontend" {
  count    = var.enable_custom_domains ? 1 : 0
  location = var.region
  name     = var.frontend_custom_domain

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.frontend.name
  }

  depends_on = [google_cloud_run_v2_service.frontend]
}

resource "google_cloud_run_domain_mapping" "main_backend" {
  count    = var.enable_custom_domains ? 1 : 0
  location = var.region
  name     = var.backend_custom_domain

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.main_backend.name
  }

  depends_on = [google_cloud_run_v2_service.main_backend]
} 