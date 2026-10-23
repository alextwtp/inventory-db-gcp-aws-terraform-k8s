variable "vpc_id" {
  type        = string
  description = "VPC ID from vpc module"
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "Public Subnets from VPC module"
}

variable "certificate_arn" {
  type        = string
  description = "ACM Certificate ARN for HTTPS listener"
}