# Outputs for Terraform configuration

output "api_url" {
  description = "URL of the API Gateway (if deployed)"
  value       = aws_api_gateway_deployment.api.invoke_url
}

output "lambda_function_name" {
  description = "Name of the Lambda function (if deployed)"
  value       = aws_lambda_function.api.function_name
}
