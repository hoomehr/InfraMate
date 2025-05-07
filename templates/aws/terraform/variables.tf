# Common variables for Terraform templates

variable "region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-west-2"
}

variable "app_name" {
  description = "Name of the application"
  type        = string
}

variable "environment" {
  description = "Environment (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

# EC2 variables
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "ami_id" {
  description = "AMI ID for EC2 instances"
  type        = string
  default     = "ami-0c55b159cbfafe1f0" # Update with appropriate AMI ID
}

variable "key_name" {
  description = "SSH key pair name"
  type        = string
  default     = null
}

# Lambda variables
variable "lambda_memory_size" {
  description = "Memory size for Lambda functions in MB"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout for Lambda functions in seconds"
  type        = number
  default     = 30
}

variable "lambda_function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = ""
}

variable "lambda_function_arn" {
  description = "ARN of the Lambda function"
  type        = string
  default     = ""
}

# Database variables
variable "database_type" {
  description = "Type of database to use (mysql, postgres, dynamodb, redis)"
  type        = string
  default     = "mysql"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  default     = "YourStrongPassword1!"  # Change this in production!
  sensitive   = true
}

variable "mongo_uri" {
  description = "MongoDB connection string"
  type        = string
  default     = "mongodb://localhost:27017/app"
  sensitive   = true
}

# VPC variables
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
}

variable "subnet_ids" {
  description = "List of subnet IDs for the application"
  type        = list(string)
  default     = []
}

# Container variables
variable "container_image" {
  description = "Container image to deploy"
  type        = string
  default     = ""
}

variable "container_port" {
  description = "Port exposed by the container"
  type        = number
  default     = 80
}

variable "health_check_path" {
  description = "Path for health check"
  type        = string
  default     = "/health"
}

# ECS variables
variable "task_cpu" {
  description = "CPU units for the task"
  type        = number
  default     = 256
}

variable "task_memory" {
  description = "Memory for the task in MB"
  type        = number
  default     = 512
}

variable "service_desired_count" {
  description = "Desired number of tasks"
  type        = number
  default     = 1
}

variable "service_min_count" {
  description = "Minimum number of tasks"
  type        = number
  default     = 1
}

variable "service_max_count" {
  description = "Maximum number of tasks"
  type        = number
  default     = 3
}

# EKS variables
variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.24"
}

variable "node_desired_size" {
  description = "Desired number of nodes"
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Minimum number of nodes"
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "Maximum number of nodes"
  type        = number
  default     = 3
}

variable "node_instance_types" {
  description = "List of instance types for nodes"
  type        = list(string)
  default     = ["t3.medium"]
}

# RDS variables
variable "db_engine" {
  description = "Database engine"
  type        = string
  default     = "mysql"
}

variable "db_engine_version" {
  description = "Database engine version"
  type        = string
  default     = "8.0"
}

variable "db_instance_class" {
  description = "Database instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Name of the database"
  type        = string
  default     = ""
}

# DynamoDB variables
variable "dynamodb_gsi_attributes" {
  description = "Map of GSI attributes and their types"
  type        = map(string)
  default     = null
}

variable "enable_dynamodb_point_in_time_recovery" {
  description = "Enable point in time recovery for DynamoDB"
  type        = bool
  default     = true
}

variable "dynamodb_ttl_attribute" {
  description = "Attribute name to use for TTL"
  type        = string
  default     = ""
}

variable "enable_dynamodb_stream" {
  description = "Enable DynamoDB stream"
  type        = bool
  default     = false
}

variable "dynamodb_stream_lambda_arn" {
  description = "ARN of Lambda function to process DynamoDB streams"
  type        = string
  default     = ""
}

# CloudFront variables
variable "cloudfront_price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100" # North America and Europe (cheapest)
}

variable "enable_alb_origin" {
  description = "Enable ALB as origin for CloudFront"
  type        = bool
  default     = false
}

variable "waf_web_acl_arn" {
  description = "ARN of WAF Web ACL"
  type        = string
  default     = ""
}

# API Gateway variables
variable "api_gateway_authorization_type" {
  description = "Authorization type for API Gateway"
  type        = string
  default     = "NONE"
}

variable "api_gateway_api_key_required" {
  description = "Whether API key is required for API Gateway"
  type        = bool
  default     = false
}

variable "api_gateway_cache_enabled" {
  description = "Enable API Gateway cache"
  type        = bool
  default     = false
}

variable "api_gateway_cache_size" {
  description = "API Gateway cache cluster size"
  type        = string
  default     = "0.5"
}

variable "api_gateway_cache_ttl" {
  description = "API Gateway cache TTL in seconds"
  type        = number
  default     = 300
}

variable "api_gateway_throttling_burst_limit" {
  description = "API Gateway throttling burst limit"
  type        = number
  default     = 5000
}

variable "api_gateway_throttling_rate_limit" {
  description = "API Gateway throttling rate limit"
  type        = number
  default     = 10000
}

# Domain variables
variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID"
  type        = string
  default     = ""
}

variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate"
  type        = string
  default     = ""
}

# Tags
variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
} 