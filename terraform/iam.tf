# Grant frontend service account permission to invoke internal services
resource "google_cloud_run_service_iam_member" "frontend_invoke_main_backend" {
  service  = google_cloud_run_v2_service.main_backend.name
  location = google_cloud_run_v2_service.main_backend.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.frontend.email}"
}

# Grant main backend service account permission to invoke microservices
resource "google_cloud_run_service_iam_member" "backend_invoke_discovery" {
  service  = google_cloud_run_v2_service.discovery.name
  location = google_cloud_run_v2_service.discovery.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.main_backend.email}"
}

resource "google_cloud_run_service_iam_member" "backend_invoke_monitoring" {
  service  = google_cloud_run_v2_service.monitoring.name
  location = google_cloud_run_v2_service.monitoring.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.main_backend.email}"
}

resource "google_cloud_run_service_iam_member" "backend_invoke_notification" {
  service  = google_cloud_run_v2_service.notification.name
  location = google_cloud_run_v2_service.notification.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.main_backend.email}"
}

# Grant service accounts permission to pull images from Artifact Registry
resource "google_artifact_registry_repository_iam_member" "service_accounts_pull" {
  for_each = {
    frontend     = google_service_account.frontend.email
    main_backend = google_service_account.main_backend.email
    discovery    = google_service_account.discovery.email
    monitoring   = google_service_account.monitoring.email
    notification = google_service_account.notification.email
  }
  
  repository = google_artifact_registry_repository.docker_repo.name
  location   = google_artifact_registry_repository.docker_repo.location
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${each.value}"
}

# Grant Cloud Build service account necessary permissions
data "google_project" "project" {
  project_id = var.project_id
}

resource "google_project_iam_member" "cloudbuild_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}

resource "google_artifact_registry_repository_iam_member" "cloudbuild_push" {
  repository = google_artifact_registry_repository.docker_repo.name
  location   = google_artifact_registry_repository.docker_repo.location
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
}