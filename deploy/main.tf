terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = "us-east-1" # Change to your preferred region
}

# VPC
resource "aws_vpc" "movie_rec_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "movie-rec-vpc"
  }
}

# Public Subnet
resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.movie_rec_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "movie-rec-public-subnet"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "movie_rec_igw" {
  vpc_id = aws_vpc.movie_rec_vpc.id

  tags = {
    Name = "movie-rec-igw"
  }
}

# Route Table
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.movie_rec_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.movie_rec_igw.id
  }

  tags = {
    Name = "movie-rec-public-rt"
  }
}

# Route Table Association
resource "aws_route_table_association" "public_rt_asso" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

# Security Group
resource "aws_security_group" "movie_rec_sg" {
  name        = "movie-rec-sg"
  description = "Security group for movie recommendation system"
  vpc_id      = aws_vpc.movie_rec_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port = 6379
    to_port   = 6379
    protocol  = "tcp"
    self      = true
  }

  ingress {
    from_port = 27017
    to_port   = 27017
    protocol  = "tcp"
    self      = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Load Balancer (for master nodes)
resource "aws_lb" "movie_rec_lb" {
  name               = "movie-rec-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.movie_rec_sg.id]
  subnets            = [aws_subnet.public_subnet.id]

  enable_deletion_protection = false

  tags = {
    Name = "movie-rec-lb"
  }
}

# Load Balancer Target Group (for master instances)
resource "aws_lb_target_group" "master_target_group" {
  name     = "master-target-group"
  port     = 5000
  protocol = "HTTP"
  vpc_id   = aws_vpc.movie_rec_vpc.id

  health_check {
    protocol = "HTTP"
    port     = "5000"
    path     = "/"
  }

  tags = {
    Name = "movie-rec-master-tg"
  }
}

# Load Balancer Listener
resource "aws_lb_listener" "lb_listener" {
  load_balancer_arn = aws_lb.movie_rec_lb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"
    fixed_response {
      status_code  = 200
      content_type = "text/plain"
      message_body = "Healthy"
    }
  }
}

# Attach master instances to the target group
resource "aws_lb_target_group_attachment" "master_attachment" {
  count            = 1 # Assuming a single master node for simplicity
  target_group_arn = aws_lb_target_group.master_target_group.arn
  target_id        = aws_instance.master.id
  port             = 5000
}

# EC2 Instances
resource "aws_instance" "master" {
  ami                    = "ami-0c7217cdde317cfec" # Amazon Linux 2 AMI ID
  instance_type          = "t2.micro"
  subnet_id              = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.movie_rec_sg.id]
  key_name               = "movie-rec-key" # Make sure to create this key pair in AWS first

  user_data = file("../ec2_setup.sh")

  tags = {
    Name = "movie-rec-master"
  }
}

resource "aws_instance" "worker" {
  count                  = 2 # Number of worker instances
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.micro"
  subnet_id              = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.movie_rec_sg.id]
  key_name               = "movie-rec-key"

  user_data = file("../ec2_setup.sh")

  tags = {
    Name = "movie-rec-worker-${count.index}"
  }
}

resource "aws_instance" "redis" {
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.micro"
  subnet_id              = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.movie_rec_sg.id]
  key_name               = "movie-rec-key"

  user_data = file("../ec2_setup.sh")

  tags = {
    Name = "movie-rec-redis"
  }
}

resource "aws_instance" "mongodb" {
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.micro"
  subnet_id              = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.movie_rec_sg.id]
  key_name               = "movie-rec-key"

  user_data = file("../ec2_setup.sh")

  tags = {
    Name = "movie-rec-mongodb"
  }
}

output "master_public_ip" {
  value = aws_instance.master.public_ip
}

output "worker_public_ips" {
  value = aws_instance.worker[*].public_ip
}

output "redis_public_ip" {
  value = aws_instance.redis.public_ip
}

output "mongodb_public_ip" {
  value = aws_instance.mongodb.public_ip
}
