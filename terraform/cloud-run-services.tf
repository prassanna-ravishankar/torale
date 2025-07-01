# Service accounts for each service
resource "google_service_account" "frontend" {
  account_id   = "${var.project_name}-frontend"
  display_name = "Frontend Service Account"
}

resource "google_service_account" "main_backend" {
  account_id   = "${var.project_name}-main-backend"
  display_name = "Main Backend Service Account"
}

resource "google_service_account" "discovery" {
  account_id   = "${var.project_name}-discovery"
  display_name = "Discovery Service Account"
}

resource "google_service_account" "monitoring" {
  account_id   = "${var.project_name}-monitoring"
  display_name = "Content Monitoring Service Account"
}

resource "google_service_account" "notification" {
  account_id   = "${var.project_name}-notification"
  display_name = "Notification Service Account"
}

# Frontend Service (Public)
resource "google_cloud_run_v2_service" "frontend" {
  name     = "${var.project_name}-frontend"
  location = var.region
  
  template {
    service_account = google_service_account.frontend.email
    
    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }
    
    containers {
      image = "${var.artifact_registry_location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}/frontend:latest"
      
      ports {
        container_port = 3000
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
          cpu    = "2"
          memory = "2Gi"
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
  
  depends_on = [
    google_project_service.required_apis,
    google_vpc_access_connector.connector
  ]
}

# Main Backend Service (Internal)
resource "google_cloud_run_v2_service" "main_backend" {
  name     = "${var.project_name}-main-backend"
  location = var.region
  
  template {
    service_account = google_service_account.main_backend.email
    
    containers {
      image = "${var.artifact_registry_location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}/backend:latest"
      
      ports {
        container_port = 8000
      }
      
      env {
        name  = "DATABASE_URL"
        value = var.database_url
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
          cpu    = "2"
          memory = "2Gi"
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
  
  depends_on = [google_project_service.required_apis]
}

# Discovery Service (Internal)
resource "google_cloud_run_v2_service" "discovery" {
  name     = "${var.project_name}-discovery"
  location = var.region
  
  template {
    service_account = google_service_account.discovery.email
    
    containers {
      image = "${var.artifact_registry_location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}/discovery-service:latest"
      
      ports {
        container_port = 8001
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
      
# Temporarily disabled for debugging
      # startup_probe {
      #   http_get {
      #     path = "/health"
      #     port = 8001
      #   }
      #   initial_delay_seconds = 10
      #   timeout_seconds = 3
      #   period_seconds = 3
      #   failure_threshold = 10
      # }
      # 
      # liveness_probe {
      #   http_get {
      #     path = "/health"
      #     port = 8001
      #   }
      #   initial_delay_seconds = 30
      #   timeout_seconds = 3
      #   period_seconds = 30
      #   failure_threshold = 3
      # }
      
      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
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
  
  ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  
  depends_on = [google_project_service.required_apis]
}

# Content Monitoring Service (Internal)
resource "google_cloud_run_v2_service" "monitoring" {
  name     = "${var.project_name}-monitoring"
  location = var.region
  
  template {
    service_account = google_service_account.monitoring.email
    
    containers {
      image = "${var.artifact_registry_location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}/content-monitoring-service:latest"
      
      ports {
        container_port = 8002
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
      
# Temporarily disabled for debugging
      # startup_probe {
      #   http_get {
      #     path = "/api/v1/health"
      #     port = 8002
      #   }
      #   initial_delay_seconds = 10
      #   timeout_seconds = 3
      #   period_seconds = 3
      #   failure_threshold = 10
      # }
      # 
      # liveness_probe {
      #   http_get {
      #     path = "/api/v1/health"
      #     port = 8002
      #   }
      #   initial_delay_seconds = 30
      #   timeout_seconds = 3
      #   period_seconds = 30
      #   failure_threshold = 3
      # }
      
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
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
  
  ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  
  depends_on = [google_project_service.required_apis]
}

# Notification Service (Internal)
resource "google_cloud_run_v2_service" "notification" {
  name     = "${var.project_name}-notification"
  location = var.region
  
  template {
    service_account = google_service_account.notification.email
    
    containers {
      image = "${var.artifact_registry_location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}/notification-service:latest"
      
      ports {
        container_port = 8003
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
      
# Temporarily disabled for debugging
      # startup_probe {
      #   http_get {
      #     path = "/health"
      #     port = 8003
      #   }
      #   initial_delay_seconds = 10
      #   timeout_seconds = 3
      #   period_seconds = 3
      #   failure_threshold = 10
      # }
      # 
      # liveness_probe {
      #   http_get {
      #     path = "/health"
      #     port = 8003
      #   }
      #   initial_delay_seconds = 30
      #   timeout_seconds = 3
      #   period_seconds = 30
      #   failure_threshold = 3
      # }
      
      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
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
  
  ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  
  depends_on = [google_project_service.required_apis]
}

# Make frontend service publicly accessible
resource "google_cloud_run_service_iam_member" "frontend_public" {
  service  = google_cloud_run_v2_service.frontend.name
  location = google_cloud_run_v2_service.frontend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Make main backend service publicly accessible
resource "google_cloud_run_service_iam_member" "main_backend_public" {
  service  = google_cloud_run_v2_service.main_backend.name
  location = google_cloud_run_v2_service.main_backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}