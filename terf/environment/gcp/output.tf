output "gcs_bucket_name" {
  description = "The name of the GCP Storage Bucket"
  value       = google_storage_bucket.my_bucket.name
}