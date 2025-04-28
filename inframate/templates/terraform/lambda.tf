# AWS Lambda Function Template
# This template creates a Lambda function with API Gateway integration

provider "aws" {
  region = var.region
}

resource "aws_lambda_function" "lambda_function" {
  function_name    = var.function_name
  handler          = var.handler
  runtime          = var.runtime
  role             = aws_iam_role.lambda_role.arn
  filename         = var.deployment_package_path
  source_code_hash = filebase64sha256(var.deployment_package_path)
  memory_size      = var.memory_size
  timeout          = var.timeout
  
  environment {
    variables = var.environment_variables
  }
  
  tags = {
    Name        = var.function_name
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM role and policy for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.function_name}-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "lambda_policy" {
  name        = "${var.function_name}-policy"
  description = "IAM policy for ${var.function_name} Lambda function"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

# API Gateway
resource "aws_api_gateway_rest_api" "api" {
  count = var.create_api_gateway ? 1 : 0
  
  name        = "${var.function_name}-api"
  description = "API Gateway for ${var.function_name}"
}

resource "aws_api_gateway_resource" "resource" {
  count = var.create_api_gateway ? 1 : 0
  
  rest_api_id = aws_api_gateway_rest_api.api[0].id
  parent_id   = aws_api_gateway_rest_api.api[0].root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "method" {
  count = var.create_api_gateway ? 1 : 0
  
  rest_api_id   = aws_api_gateway_rest_api.api[0].id
  resource_id   = aws_api_gateway_resource.resource[0].id
  http_method   = "ANY"
  authorization_type = "NONE"
}

resource "aws_api_gateway_integration" "integration" {
  count = var.create_api_gateway ? 1 : 0
  
  rest_api_id = aws_api_gateway_rest_api.api[0].id
  resource_id = aws_api_gateway_resource.resource[0].id
  http_method = aws_api_gateway_method.method[0].http_method
  
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.lambda_function.invoke_arn
}

resource "aws_api_gateway_deployment" "deployment" {
  count = var.create_api_gateway ? 1 : 0
  
  depends_on = [
    aws_api_gateway_integration.integration
  ]
  
  rest_api_id = aws_api_gateway_rest_api.api[0].id
  stage_name  = var.api_stage_name
}

resource "aws_lambda_permission" "apigw_permission" {
  count = var.create_api_gateway ? 1 : 0
  
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.function_name
  principal     = "apigateway.amazonaws.com"
  
  source_arn = "${aws_api_gateway_rest_api.api[0].execution_arn}/*/*"
}

# Variables
variable "region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "runtime" {
  description = "Runtime for the Lambda function"
  type        = string
  default     = "python3.9"
}

variable "handler" {
  description = "Handler for the Lambda function"
  type        = string
  default     = "index.handler"
}

variable "deployment_package_path" {
  description = "Path to the deployment package (ZIP file)"
  type        = string
}

variable "memory_size" {
  description = "Memory size for the Lambda function in MB"
  type        = number
  default     = 128
}

variable "timeout" {
  description = "Timeout for the Lambda function in seconds"
  type        = number
  default     = 30
}

variable "environment_variables" {
  description = "Environment variables for the Lambda function"
  type        = map(string)
  default     = {}
}

variable "create_api_gateway" {
  description = "Whether to create an API Gateway for the Lambda"
  type        = bool
  default     = true
}

variable "api_stage_name" {
  description = "Stage name for the API Gateway"
  type        = string
  default     = "prod"
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
output "lambda_function_arn" {
  value = aws_lambda_function.lambda_function.arn
}

output "api_endpoint" {
  value = var.create_api_gateway ? aws_api_gateway_deployment.deployment[0].invoke_url : null
} 