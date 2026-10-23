variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-1"
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
  default     = "793012896705"
}

variable "db_password" {
  description = "RDS password"
  type        = string
  sensitive   = true
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}