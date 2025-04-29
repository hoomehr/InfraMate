# Common variables for Terraform templates

variable "region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "app"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

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

variable "subnet_ids" {
  description = "List of subnet IDs for the application"
  type        = list(string)
  default     = []
} 