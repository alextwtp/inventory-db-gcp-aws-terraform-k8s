# 1. 建立 VPC
resource "aws_vpc" "my_vpc" {
  cidr_block           = "10.0.0.0/16" 
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "main-vpc"
  }
}

# 2. 建立公有子網路 (Public Subnet - 給 ALB / ECS 部署用)
resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.my_vpc.id
  cidr_block              = "10.0.0.0/24" 
  map_public_ip_on_launch = true
  availability_zone       = "${var.aws_region}a"

  tags = {
    Name = "public-subnet"
  }
}

# 3. 建立網際網路閘道 (Internet Gateway - 讓外網能連進來)
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.my_vpc.id

  tags = {
    Name = "main-igw"
  }
}

# 4. 建立路由表 (Route Table) 並綁定 IGW
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.my_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "public-route-table"
  }
}

# 5. 綁定路由表至 Public Subnet
resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

# 6. 建立第二個 Subnet (位於不同 AZ，例如 ap-northeast-2c)
resource "aws_subnet" "public_subnet_2" {
  vpc_id                  = aws_vpc.my_vpc.id
  cidr_block              = "10.0.2.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "${var.aws_region}c" # 注意這裡是 c 區

  tags = {
    Name = "public-subnet-2"
  }
}

# 7. 綁定第二個 Subnet 到路由表
resource "aws_route_table_association" "public_assoc_2" {
  subnet_id      = aws_subnet.public_subnet_2.id
  route_table_id = aws_route_table.public_rt.id
}

# 8. 建立 RDS 專用的 DB Subnet Group
resource "aws_db_subnet_group" "rds_subnet_group" {  
  name = "main-rds-subnet-group-v2"
  subnet_ids = [aws_subnet.public_subnet.id, aws_subnet.public_subnet_2.id]

  tags = {
    Name = "Main RDS Subnet Group"
  }
}
