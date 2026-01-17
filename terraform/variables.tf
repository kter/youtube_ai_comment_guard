variable "project_ids" {
  description = "GCP Project IDs per environment"
  type        = map(string)
  default = {
    dev = "youtube-ai-comment-guard-dev"
    prd = "youtube-ai-comment-guard-prd"
  }
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

# AWS Configuration
variable "aws_region" {
  description = "AWS Region for frontend hosting"
  type        = string
  default     = "ap-northeast-1"
}

variable "frontend_domains" {
  description = "Frontend domain names per environment"
  type        = map(string)
  default = {
    dev = "youtube-comment-guard.dev.devtools.site"
    prd = "youtube-comment-guard.devtools.site"
  }
}

variable "route53_zone_names" {
  description = "Route 53 Hosted Zone names per environment"
  type        = map(string)
  default = {
    dev = "dev.devtools.site"
    prd = "devtools.site"
  }
}
