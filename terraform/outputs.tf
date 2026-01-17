output "backend_url" {
  description = "Backend API URL"
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  description = "Frontend URL"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "firestore_database" {
  description = "Firestore database name"
  value       = google_firestore_database.main.name
}
