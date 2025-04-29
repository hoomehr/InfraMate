# Terraform template for microservices architecture on AWS
provider "aws" {
  region = var.region
}

locals {
  name_prefix = "${var.app_name}-${var.environment}"
}

# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${local.name_prefix}-vpc"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${local.name_prefix}-public-subnet-${count.index}"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${local.name_prefix}-private-subnet-${count.index}"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-igw"
  }
}

# Elastic IP for NAT Gateway
resource "aws_eip" "nat" {
  count      = 2
  domain     = "vpc"
  depends_on = [aws_internet_gateway.main]

  tags = {
    Name = "${local.name_prefix}-nat-eip-${count.index}"
  }
}

# NAT Gateway
resource "aws_nat_gateway" "main" {
  count         = 2
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "${local.name_prefix}-nat-gw-${count.index}"
  }
}

# Route Table for Public Subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${local.name_prefix}-public-rt"
  }
}

# Route Table Association for Public Subnets
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Route Tables for Private Subnets
resource "aws_route_table" "private" {
  count  = 2
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name = "${local.name_prefix}-private-rt-${count.index}"
  }
}

# Route Table Association for Private Subnets
resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Security Group for services
resource "aws_security_group" "services" {
  name        = "${local.name_prefix}-services-sg"
  description = "Security group for microservices"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port       = 0
    to_port         = 0
    protocol        = "-1"
    security_groups = [aws_security_group.alb.id]
  }

  tags = {
    Name = "${local.name_prefix}-services-sg"
  }
}

# Security Group for ALB
resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb-sg"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name_prefix}-alb-sg"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = false

  tags = {
    Name = "${local.name_prefix}-alb"
  }
}

# ALB Target Groups for services
resource "aws_lb_target_group" "services" {
  for_each = var.microservices

  name     = "${local.name_prefix}-${each.key}-tg"
  port     = each.value.port
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    path                = each.value.health_check_path
    port                = each.value.port
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name = "${local.name_prefix}-${each.key}-tg"
  }
}

# ALB Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "Service not found"
      status_code  = "404"
    }
  }
}

# ALB Listener Rules for each service
resource "aws_lb_listener_rule" "services" {
  for_each = var.microservices

  listener_arn = aws_lb_listener.http.arn
  priority     = each.value.priority

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.services[each.key].arn
  }

  condition {
    path_pattern {
      values = [each.value.path_pattern]
    }
  }
}

# ECR Repositories for each service
resource "aws_ecr_repository" "services" {
  for_each = var.microservices

  name                 = "${local.name_prefix}-${each.key}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${local.name_prefix}-${each.key}"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${local.name_prefix}-cluster"
  }
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution" {
  name = "${local.name_prefix}-ecs-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${local.name_prefix}-ecs-task-execution"
  }
}

# IAM Policy Attachment for ECS Task Execution
resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Definitions for each service
resource "aws_ecs_task_definition" "services" {
  for_each = var.microservices

  family                   = "${local.name_prefix}-${each.key}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = each.value.cpu
  memory                   = each.value.memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([
    {
      name      = each.key
      image     = "${aws_ecr_repository.services[each.key].repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = each.value.port
          hostPort      = each.value.port
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${local.name_prefix}-${each.key}"
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "${local.name_prefix}-${each.key}"
  }
}

# CloudWatch Log Groups for each service
resource "aws_cloudwatch_log_group" "services" {
  for_each = var.microservices

  name              = "/ecs/${local.name_prefix}-${each.key}"
  retention_in_days = 30

  tags = {
    Name = "${local.name_prefix}-${each.key}-logs"
  }
}

# ECS Services
resource "aws_ecs_service" "services" {
  for_each = var.microservices

  name            = each.key
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.services[each.key].arn
  launch_type     = "FARGATE"
  desired_count   = each.value.desired_count

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.services.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.services[each.key].arn
    container_name   = each.key
    container_port   = each.value.port
  }

  depends_on = [aws_lb_listener.http]

  tags = {
    Name = "${local.name_prefix}-${each.key}-service"
  }
}

# DynamoDB Table for shared database (for services that need a database)
resource "aws_dynamodb_table" "main" {
  name         = "${local.name_prefix}-db"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  tags = {
    Name = "${local.name_prefix}-db"
  }
}

# Redis (ElastiCache) for caching/messaging
resource "aws_elasticache_subnet_group" "main" {
  name       = "${local.name_prefix}-redis-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${local.name_prefix}-redis-subnet-group"
  }
}

resource "aws_security_group" "redis" {
  name        = "${local.name_prefix}-redis-sg"
  description = "Security group for Redis"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.services.id]
  }

  tags = {
    Name = "${local.name_prefix}-redis-sg"
  }
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "${local.name_prefix}-redis"
  description                = "Redis for microservices"
  node_type                  = "cache.t3.small"
  port                       = 6379
  parameter_group_name       = "default.redis6.x.cluster.on"
  automatic_failover_enabled = true
  subnet_group_name          = aws_elasticache_subnet_group.main.name
  security_group_ids         = [aws_security_group.redis.id]
  num_node_groups            = 1
  replicas_per_node_group    = 1

  tags = {
    Name = "${local.name_prefix}-redis"
  }
}

# SNS Topic for inter-service communication
resource "aws_sns_topic" "events" {
  name = "${local.name_prefix}-events"

  tags = {
    Name = "${local.name_prefix}-events"
  }
}

# SQS Queues for each service that needs one
resource "aws_sqs_queue" "services" {
  for_each = {
    for k, v in var.microservices : k => v
    if lookup(v, "needs_queue", false)
  }

  name                      = "${local.name_prefix}-${each.key}-queue"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 345600 # 4 days
  receive_wait_time_seconds = 10

  tags = {
    Name = "${local.name_prefix}-${each.key}-queue"
  }
}

# SNS Subscription for services with queues
resource "aws_sns_topic_subscription" "services" {
  for_each = {
    for k, v in var.microservices : k => v
    if lookup(v, "needs_queue", false)
  }

  topic_arn = aws_sns_topic.events.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.services[each.key].arn
}

# SQS Queue Policy for SNS messages
resource "aws_sqs_queue_policy" "services" {
  for_each = {
    for k, v in var.microservices : k => v
    if lookup(v, "needs_queue", false)
  }

  queue_url = aws_sqs_queue.services[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "sns.amazonaws.com"
        }
        Action    = "sqs:SendMessage"
        Resource  = aws_sqs_queue.services[each.key].arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_sns_topic.events.arn
          }
        }
      }
    ]
  })
}

# API Gateway for public-facing services
resource "aws_api_gateway_rest_api" "main" {
  name        = "${local.name_prefix}-api"
  description = "API Gateway for microservices"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name = "${local.name_prefix}-api"
  }
}

# Data source for available AWS AZs
data "aws_availability_zones" "available" {
  state = "available"
}

# Outputs
output "alb_dns_name" {
  description = "DNS name of the ALB"
  value       = aws_lb.main.dns_name
}

output "ecr_repository_urls" {
  description = "URLs of the ECR repositories"
  value = {
    for k, v in aws_ecr_repository.services : k => v.repository_url
  }
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.main.name
}

output "redis_endpoint" {
  description = "Endpoint of the Redis cluster"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic"
  value       = aws_sns_topic.events.arn
}

output "sqs_queue_urls" {
  description = "URLs of the SQS queues"
  value = {
    for k, v in aws_sqs_queue.services : k => v.url
  }
} 