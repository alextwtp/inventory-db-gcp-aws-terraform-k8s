output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "alb_zone_id" {
  value = aws_lb.main.zone_id
}

output "alb_arn" {
  value = aws_lb.main.arn
}

output "target_group_arn" {
  value = aws_lb_target_group.ecs_tg.arn
}

output "alb_listener_http" {
  value = aws_lb_listener.http
}

output "ecs_sg_id" {
  value = aws_security_group.ecs_sg.id
}