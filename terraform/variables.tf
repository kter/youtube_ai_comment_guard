variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region for Cloud Run"
  type        = string
  default     = "asia-northeast1"
}

variable "firestore_location" {
  description = "Firestore location"
  type        = string
  default     = "asia-northeast1"
}

variable "backend_image" {
  description = "Docker image for backend API"
  type        = string
  default     = "gcr.io/cloudrun/placeholder"
}

variable "frontend_image" {
  description = "Docker image for frontend"
  type        = string
  default     = "gcr.io/cloudrun/placeholder"
}
