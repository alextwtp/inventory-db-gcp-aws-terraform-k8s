# 1. 建立 Application Load Balancer
resource "aws_lb" "main" {
  name               = "tf-ecs-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets = var.public_subnet_ids
  tags = {
    Name = "tf-ecs-alb"
  }                 
}

# 2. Create Target Group
resource "aws_lb_target_group" "ecs_tg" {
  name = "tf-ecs-target-group-v2"
  port        = 80
  protocol    = "HTTP"
  vpc_id = var.vpc_id  
  target_type = "ip" # Fargate mode must use IP type
  lifecycle {
    create_before_destroy = true
  }
  health_check {
    path                = "/"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }
}

# 3. HTTP Listener (Port 80) -> 301 redirect to HTTPS Automatically
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "forward"
    target_group_arn = aws_lb_target_group.ecs_tg.arn
  }  
}

# 4. HTTPS Listener (Port 443) -> Mount ACM certificate and forward to Target Group
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  
  # Make sure to use the variable that was just passed in
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ecs_tg.arn
  }
}

