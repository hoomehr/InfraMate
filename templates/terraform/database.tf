# Terraform template for database resources
provider "aws" {
  region = var.region
}

# RDS instance
resource "aws_db_instance" "mysql" {
  count               = var.database_type == "mysql" ? 1 : 0
  allocated_storage   = 20
  storage_type        = "gp2"
  engine              = "mysql"
  engine_version      = "8.0"
  instance_class      = "db.t3.micro"
  identifier          = "${var.app_name}-${var.environment}"
  db_name             = replace(var.app_name, "-", "_")
  username            = var.db_username
  password            = var.db_password
  skip_final_snapshot = true
  
  tags = {
    Name        = "${var.app_name}-db"
    Environment = var.environment
  }
}

# PostgreSQL RDS instance
resource "aws_db_instance" "postgres" {
  count               = var.database_type == "postgres" ? 1 : 0
  allocated_storage   = 20
  storage_type        = "gp2"
  engine              = "postgres"
  engine_version      = "14"
  instance_class      = "db.t3.micro"
  identifier          = "${var.app_name}-${var.environment}"
  db_name             = replace(var.app_name, "-", "_")
  username            = var.db_username
  password            = var.db_password
  skip_final_snapshot = true
  
  tags = {
    Name        = "${var.app_name}-db"
    Environment = var.environment
  }
}

# Security group for RDS
resource "aws_security_group" "database" {
  count       = var.database_type == "mysql" || var.database_type == "postgres" ? 1 : 0
  name        = "${var.app_name}-${var.environment}-db-sg"
  description = "Security group for ${var.app_name} database"
  
  ingress {
    from_port       = var.database_type == "mysql" ? 3306 : 5432
    to_port         = var.database_type == "mysql" ? 3306 : 5432
    protocol        = "tcp"
    cidr_blocks     = ["10.0.0.0/16"]
    description     = "DB access from internal network"
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
  
  tags = {
    Name        = "${var.app_name}-db-sg"
    Environment = var.environment
  }
}

# DynamoDB table
resource "aws_dynamodb_table" "table" {
  count          = var.database_type == "dynamodb" ? 1 : 0
  name           = "${var.app_name}-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"
  
  attribute {
    name = "id"
    type = "S"
  }
  
  tags = {
    Name        = "${var.app_name}-table"
    Environment = var.environment
  }
}

# ElastiCache Redis cluster
resource "aws_elasticache_cluster" "redis" {
  count                = var.database_type == "redis" ? 1 : 0
  cluster_id           = "${var.app_name}-${var.environment}"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis6.x"
  engine_version       = "6.2"
  port                 = 6379
  
  tags = {
    Name        = "${var.app_name}-redis"
    Environment = var.environment
  }
}

# Security group for Redis
resource "aws_security_group" "redis" {
  count       = var.database_type == "redis" ? 1 : 0
  name        = "${var.app_name}-${var.environment}-redis-sg"
  description = "Security group for ${var.app_name} Redis"
  
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    cidr_blocks     = ["10.0.0.0/16"]
    description     = "Redis access from internal network"
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
  
  tags = {
    Name        = "${var.app_name}-redis-sg"
    Environment = var.environment
  }
} 