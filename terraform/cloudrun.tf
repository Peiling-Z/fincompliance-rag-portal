resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "fincompliance-rag-portal-repo"
  format        = "DOCKER"
}

resource "google_cloud_run_service" "service" {
  name     = "fincompliance-rag-portal-svc"
  location = var.region
  template {
    spec {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/fincompliance-rag-portal-repo/fincompliance-rag-portal:latest"
        ports { container_port = 8000 }
      }
    }
  }
  traffic { percent = 100, latest_revision = true }
}
