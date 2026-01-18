terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = local.project_id
  region  = var.region
}

# AWS Provider - Default region
provider "aws" {
  region  = var.aws_region
  profile = local.environment # dev or prd profile

  default_tags {
    tags = {
      Project     = "YouTube Comment Guard"
      Environment = local.environment
      ManagedBy   = "Terraform"
    }
  }
}

# AWS Provider - us-east-1 (CloudFront ACM certificates require us-east-1)
provider "aws" {
  alias   = "us_east_1"
  region  = "us-east-1"
  profile = local.environment # dev or prd profile

  default_tags {
    tags = {
      Project     = "YouTube Comment Guard"
      Environment = local.environment
      ManagedBy   = "Terraform"
    }
  }
}

locals {
  environment = terraform.workspace
  project_id  = var.project_ids[local.environment]
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
resource "google_firestore_index" "comments_category_toxicity_published" {
  project    = local.project_id
  database   = google_firestore_database.main.name
  collection = "comments"

  fields {
    field_path = "category"
    order      = "ASCENDING"
  }

  fields {
    field_path = "published_at"
    order      = "DESCENDING"
  }

  fields {
    field_path = "toxicity_score"
    order      = "DESCENDING"
  }
}

resource "google_secret_manager_secret" "youtube_credentials" {
  secret_id = "youtube-oauth-credentials"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "youtube_client_id" {
  secret_id = "youtube-client-id"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "youtube_client_secret" {
  secret_id = "youtube-client-secret"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "session_secret_key" {
  secret_id = "session-secret-key"

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
  project = local.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_project_iam_member" "cloud_run_aiplatform" {
  project = local.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_project_iam_member" "cloud_run_secretmanager" {
  project = local.project_id
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
      image = "asia-northeast1-docker.pkg.dev/${local.project_id}/youtube-guard/backend:latest"

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = local.project_id
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

      env {
        name  = "FRONTEND_URL"
        value = "https://${var.frontend_domains[local.environment]}"
      }

      env {
        name = "YOUTUBE_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.youtube_client_id.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "YOUTUBE_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.youtube_client_secret.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "SESSION_SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.session_secret_key.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true # リクエストベース課金（CPU idle時は課金されない）
      }
    }

    scaling {
      min_instance_count = local.current_scaling.min_instance_count
      max_instance_count = local.current_scaling.max_instance_count
    }
  }

  depends_on = [google_project_service.apis]
}

# Frontend is now hosted on AWS CloudFront + S3
# See aws_frontend.tf for frontend infrastructure

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
