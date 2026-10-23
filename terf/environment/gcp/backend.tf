terraform {
  backend "gcs" {
    bucket = "my-tf-state-gcp"
    prefix = "fastapi/gcp"
  }
}