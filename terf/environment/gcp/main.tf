# 1. 建立 Artifact Registry 儲存庫 (存放 Docker Image)
resource "google_artifact_registry_repository" "my_repo" {
  location      = var.gcp_region
  repository_id = "${var.app_name}-repo"
  description   = "Docker repository for FastAPI"
  format        = "DOCKER"
}

# 2. 建立 Cloud Run 服務
resource "google_cloud_run_v2_service" "default" {
  name     = "${var.app_name}-service"
  location = var.gcp_region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      # 使用官方占位圖片，避免第一次 terraform apply 因為找不到尚未 build 的鏡像而報錯
      image = "gcr.io/cloudrun/hello"      
      ports {
        container_port = 8000
      }
    }
  }
}

# 3. 設定 Cloud Run 為公開存取 (允許所有人訪問)
resource "google_cloud_run_v2_service_iam_member" "noauth" {
  location = google_cloud_run_v2_service.default.location
  name     = google_cloud_run_v2_service.default.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# 1. 建立 GCP Cloud SQL (MySQL) 實體
resource "google_sql_database_instance" "main" {
  name             = "${var.app_name}-db"
  database_version = "MYSQL_8_0"
  region           = var.gcp_region
  deletion_protection = false # 方便測試，若要在生產環境可設為 true

  settings {
    tier = "db-f1-micro" # 測試用的輕量等級
  }
}

# 2. 建立資料庫
resource "google_sql_database" "database" {
  name     = "inventory_db"
  instance = google_sql_database_instance.main.name
}

# 3. 建立使用者並設定密碼
resource "google_sql_user" "users" {
  name     = var.db_username
  instance = google_sql_database_instance.main.name
  password = var.db_password
}

# 建立 GCP Cloud Storage Bucket (類似 AWS S3)
resource "google_storage_bucket" "my_bucket" {
  name                     = "${var.gcp_project_id}-${var.app_name}-storage" # Bucket 名稱全域必須唯一
  location                 = var.gcp_region
  force_destroy            = true  # 測試用：當刪除 bucket 時連同裡面的檔案一併刪除
  public_access_prevention = "enforced" # 防護機制：禁止公開存取，確保安全性

  uniform_bucket_level_access = true # 採用統一存取控制權限 (建議最佳實踐)
}