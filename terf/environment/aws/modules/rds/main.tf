# 1. Security Group dedicated to RDS
resource "aws_security_group" "rds_sg" {
  name        = "rds-security-group"
  description = "Allow inbound traffic from ECS tasks only"
  vpc_id      = var.vpc_id
  
  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [var.ecs_sg_id]
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

# 2. RDS Subnet Group
resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "main-rds-subnet-group-v2"
  subnet_ids = var.subnet_ids

  tags = {
    Name = "My RDS Subnet Group"
  }
}

# 3. Create RDS MySQL Database Instance
resource "aws_db_instance" "my_db" {
  identifier             = "my-inventory-db"
  allocated_storage      = 20
  max_allocated_storage  = 100
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t4g.micro"
  
  db_name                = "inventory_db"
  username               = "admin"
  password               = var.db_password
    
  vpc_security_group_ids = [aws_security_group.rds_sg.id]   
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name 
  skip_final_snapshot    = true

  tags = {
    Name = "my-production-db"
  }
}

