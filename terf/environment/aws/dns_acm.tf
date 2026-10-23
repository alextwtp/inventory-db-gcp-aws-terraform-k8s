# 1. Automatically create Route 53 Hosted Zone
resource "aws_route53_zone" "main" {
  name          = "alextwtp.online"
  force_destroy = true
}

# 2. Output Route 53 Name Servers (NS)
output "name_servers" {
  value       = aws_route53_zone.main.name_servers
  description = "Please paste these 4 NS records into domain registrar custom DNS if needed"
}

# 3. Apply for ACM SSL Free Certificate
resource "aws_acm_certificate" "cert" {
  domain_name       = "alextwtp.online"
  validation_method = "DNS"

  subject_alternative_names = [
    "*.alextwtp.online"
  ]

  lifecycle {
    create_before_destroy = true
  }
}

# 4. Automatically create ACM DNS validation CNAME records
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.cert.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.main.zone_id
}

# 5. Wait for ACM certificate issuance to complete
resource "aws_acm_certificate_validation" "cert" {
  certificate_arn         = aws_acm_certificate.cert.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

# 6. Set A Record to point to ALB
resource "aws_route53_record" "www" {
  zone_id = aws_route53_zone.main.zone_id
  name    = ""
  type    = "A"

  alias {
    name                   = module.alb.alb_dns_name
    zone_id                = module.alb.alb_zone_id
    evaluate_target_health = true
  }
}