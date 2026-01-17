terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  environment = terraform.workspace
  name_prefix = "youtube-guard-${local.environment}"

  # 環境別のスケーリング設定
  scaling_config = {
    dev = {
      min_instance_count = 0
      max_instance_count = 1
    }
    prd = {
      min_instance_count = 0
      max_instance_count = 5
    }
    default = {
      min_instance_count = 0
      max_instance_count = 2
    }
  }

  # ワークスペースに基づくスケーリング設定の取得（存在しない場合はdefault）
  current_scaling = lookup(local.scaling_config, local.environment, local.scaling_config.default)
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "firestore.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudscheduler.googleapis.com",
    "aiplatform.googleapis.com",
    "youtube.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# Firestore Database
resource "google_firestore_database" "main" {
  name        = "(default)"
  location_id = var.firestore_location
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.apis]
}

# Secret Manager - YouTube OAuth credentials
resource "google_secret_manager_secret" "youtube_credentials" {
  secret_id = "youtube-oauth-credentials"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run" {
  account_id   = "youtube-guard-runner"
  display_name = "YouTube Comment Guard Cloud Run Service Account"
}

# IAM bindings for Service Account
resource "google_project_iam_member" "cloud_run_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_project_iam_member" "cloud_run_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_project_iam_member" "cloud_run_secretmanager" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Cloud Run - Backend API
resource "google_cloud_run_v2_service" "backend" {
  name     = "${local.name_prefix}-api"
  location = var.region

  template {
    service_account = google_service_account.cloud_run.email

    containers {
      image = var.backend_image

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "ENVIRONMENT"
        value = local.environment
      }

      env {
        name = "YOUTUBE_CREDENTIALS"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.youtube_credentials.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true  # リクエストベース課金（CPU idle時は課金されない）
      }
    }

    scaling {
      min_instance_count = local.current_scaling.min_instance_count
      max_instance_count = local.current_scaling.max_instance_count
    }
  }

  depends_on = [google_project_service.apis]
}

# Cloud Run - Frontend
resource "google_cloud_run_v2_service" "frontend" {
  name     = "${local.name_prefix}-frontend"
  location = var.region

  template {
    containers {
      image = var.frontend_image

      env {
        name  = "VITE_API_URL"
        value = google_cloud_run_v2_service.backend.uri
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true  # リクエストベース課金（CPU idle時は課金されない）
      }
    }

    scaling {
      min_instance_count = local.current_scaling.min_instance_count
      max_instance_count = local.current_scaling.max_instance_count
    }
  }

  depends_on = [google_project_service.apis]
}

# Allow unauthenticated access to frontend
resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  name     = google_cloud_run_v2_service.frontend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Allow unauthenticated access to backend (secured by OAuth)
resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  name     = google_cloud_run_v2_service.backend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Service Account for Cloud Scheduler
resource "google_service_account" "scheduler" {
  account_id   = "youtube-guard-scheduler"
  display_name = "YouTube Comment Guard Scheduler"
}

resource "google_cloud_run_v2_service_iam_member" "scheduler_invoker" {
  name     = google_cloud_run_v2_service.backend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

# Cloud Scheduler - Periodic processing job
resource "google_cloud_scheduler_job" "process_comments" {
  name        = "youtube-guard-process-comments"
  description = "Trigger comment processing every 15 minutes"
  schedule    = "*/15 * * * *"
  time_zone   = "Asia/Tokyo"

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.backend.uri}/api/scheduler/process"

    oidc_token {
      service_account_email = google_service_account.scheduler.email
    }
  }

  depends_on = [google_project_service.apis]
}
