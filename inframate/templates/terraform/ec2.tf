# EC2 Instance Template
# This template creates an EC2 instance with customizable parameters

provider "aws" {
  region = var.region
}

resource "aws_instance" "app_server" {
  ami           = var.ami_id
  instance_type = var.instance_type
  key_name      = var.key_name
  
  vpc_security_group_ids = [aws_security_group.app_sg.id]
  subnet_id              = var.subnet_id
  
  tags = {
    Name        = var.instance_name
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_security_group" "app_sg" {
  name        = "${var.instance_name}-sg"
  description = "Security group for ${var.instance_name} instance"
  vpc_id      = var.vpc_id
  
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH access"
  }
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP access"
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS access"
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
  
  tags = {
    Name        = "${var.instance_name}-sg"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Variables
variable "region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "ami_id" {
  description = "AMI ID for the EC2 instance"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "key_name" {
  description = "SSH key name"
  type        = string
  default     = null
}

variable "vpc_id" {
  description = "VPC ID to deploy the resources"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID to deploy the EC2 instance"
  type        = string
}

variable "instance_name" {
  description = "Name for the EC2 instance"
  type        = string
  default     = "app-server"
}

variable "environment" {
  description = "Environment (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "inframate-project"
}

# Outputs
output "instance_id" {
  value = aws_instance.app_server.id
}

output "instance_public_ip" {
  value = aws_instance.app_server.public_ip
}

output "security_group_id" {
  value = aws_security_group.app_sg.id
} 