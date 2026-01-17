output "backend_url" {
  description = "Backend API URL"
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  description = "Frontend URL (CloudFront)"
  value       = "https://${local.frontend_domain}"
}

output "frontend_cloudfront_domain" {
  description = "CloudFront distribution domain"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "frontend_bucket_name" {
  description = "S3 bucket name for frontend deployment"
  value       = aws_s3_bucket.frontend.bucket
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID for cache invalidation"
  value       = aws_cloudfront_distribution.frontend.id
}

output "firestore_database" {
  description = "Firestore database name"
  value       = google_firestore_database.main.name
}
