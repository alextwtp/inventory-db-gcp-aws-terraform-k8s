provider "aws" {
  region = "ap-northeast-1"
}

# 1. VPC Module
module "vpc" {
  source     = "./modules/vpc"
  aws_region = "ap-northeast-1"
}

# 2. ALB Module
module "alb" {
  source            = "./modules/alb"
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids

  certificate_arn   = aws_acm_certificate_validation.cert.certificate_arn

  depends_on = [
    aws_acm_certificate_validation.cert
  ]
}

# 3. RDS Security Group
resource "aws_security_group" "rds_sg" {
  name        = "rds-security-group"
  description = "Allow inbound traffic for RDS"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "rds-sg"
  }
}

# 5. RDS MySQL 8.0 Setting
resource "aws_db_instance" "my_db" {
  identifier            = "my-inventory-db-2"
  allocated_storage     = 20
  max_allocated_storage = 100
  engine                = "mysql"
  engine_version        = "8.0"  
  instance_class        = "db.t4g.micro"
  
  db_name               = "inventory_db"
  username              = "admin"
  password              = var.db_password
    
  vpc_security_group_ids = [aws_security_group.rds_sg.id]  
  db_subnet_group_name = "main-rds-subnet-group-v2" 
  skip_final_snapshot    = true

  tags = {
    Name = "my-production-db"
  }
}

# ==============================================================================
# Security Infrastructure (ACM & KMS CMK with Automatic Rotation)

# Note: ACM Certificates and KMS CMKs were initially provisioned via AWS Console.
# To avoid State Drift and resource conflicts in the current environment, 
# this block is kept as reference code for future automated multi-account rebuilds.
# ==============================================================================

# 6. ESTABLISH ACM Certificate 
# a. Build New CMK 
resource "aws_kms_key" "my_new_app_cmk" {
  description             = "CMK for My New Project Data Encryption" # Update the description for the new project
  deletion_window_in_days = 7                                        # 7 days is recommended for practice/test environments for easier cleanup
  enable_key_rotation     = true                                     # Ｅnable automatic key rotation for security best practices

  tags = {
    Environment = "Development"
    Project     = "NewProject"
    ManagedBy   = "Terraform"
  }
}

# b. Build New KMS Alias
resource "aws_kms_alias" "my_new_app_cmk_alias" {
  name          = "alias/my-second-app-key"                  # The alias for the new KMS key (keep the alias/ prefix)  
  target_key_id = aws_kms_key.my_new_app_cmk.key_id       # Automatically reference the key ID built above 　　　　
}