# 1. Establish ECR Repository
resource "aws_ecr_repository" "app_repo" {
  name                 = "my-app-repo" 
  force_delete         = true
  image_tag_mutability = "MUTABLE"

  # Open image vulnerability scanning (security best practice)
  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}

# Export ECR URL, for future use in CI/CD or Docker Push
output "ecr_repository_url" {
  value       = aws_ecr_repository.app_repo.repository_url
  description = "The URL of the ECR repository"
}