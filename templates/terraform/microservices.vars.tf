variable "region" {
  description = "The AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "app_name" {
  description = "The name of the application"
  type        = string
}

variable "environment" {
  description = "The environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "microservices" {
  description = "Map of microservices configurations"
  type = map(object({
    port              = number
    health_check_path = string
    path_pattern      = string
    priority          = number
    cpu               = number
    memory            = number
    desired_count     = number
    needs_queue       = optional(bool, false)
  }))
  default = {
    api = {
      port              = 3000
      health_check_path = "/health"
      path_pattern      = "/api/*"
      priority          = 100
      cpu               = 256
      memory            = 512
      desired_count     = 2
    },
    auth = {
      port              = 3001
      health_check_path = "/health"
      path_pattern      = "/auth/*"
      priority          = 200
      cpu               = 256
      memory            = 512
      desired_count     = 2
    },
    worker = {
      port              = 3002
      health_check_path = "/health"
      path_pattern      = "/worker/*"
      priority          = 300
      cpu               = 256
      memory            = 512
      desired_count     = 1
      needs_queue       = true
    }
  }
} 