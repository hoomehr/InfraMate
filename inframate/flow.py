"""Main Inframate flow logic"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List

from inframate.analyzers.repository import analyze_repository
from inframate.agents.ai_analyzer import analyze_with_ai, fallback_analyze
from inframate.utils.rag import RAGManager

def read_inframate_file(repo_path: str) -> Dict[str, Any]:
    """Read and parse the inframate.md file"""
    inframate_path = Path(repo_path) / "inframate.md"
    if not inframate_path.exists():
        raise FileNotFoundError("inframate.md file not found in repository")
    
    with open(inframate_path, "r") as f:
        content = f.read()
    
    # Basic parsing of markdown content
    sections = content.split("##")
    info = {}
    for section in sections[1:]:  # Skip the first empty section
        lines = section.strip().split("\n")
        title = lines[0].strip()
        content = "\n".join(lines[1:]).strip()
        info[title.lower()] = content
    
    return info

def generate_terraform_template(md_data: Dict[str, Any], services: List[str]) -> str:
    """Generate Terraform template based on detected services"""
    # Detect the proper template to use
    language = md_data.get("language", "").lower()
    framework = md_data.get("framework", "").lower()
    
    if "node" in language and "express" in framework:
        return generate_nodejs_terraform(md_data)
    elif "python" in language:
        return generate_python_terraform(md_data)
    else:
        return generate_generic_terraform(md_data)

def generate_nodejs_terraform(md_data: Dict[str, Any]) -> str:
    """Generate Terraform for Node.js/Express applications"""
    return """# Terraform configuration for Node.js/Express API
provider "aws" {
  region = var.region
}

# Lambda function for the Express.js API
resource "aws_lambda_function" "api" {
  function_name    = "${var.app_name}-${var.environment}"
  handler          = "src/lambda.handler"
  runtime          = "nodejs18.x"
  filename         = "${path.module}/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda.zip")
  role             = aws_iam_role.lambda_role.arn
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory_size
  
  environment {
    variables = {
      NODE_ENV = var.environment
      MONGO_URI = var.mongo_uri
    }
  }
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.app_name}-${var.environment}-lambda-role"
  
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

# API Gateway
resource "aws_api_gateway_rest_api" "api" {
  name        = "${var.app_name}-${var.environment}-api"
  description = "API Gateway for ${var.app_name}"
}

# Set up a proxy resource to catch all requests
resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "{proxy+}"
}

# ANY method for the proxy resource
resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization_type = "NONE"
}

# Deploy the API
resource "aws_api_gateway_deployment" "api" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = var.environment
  
  depends_on = [
    aws_api_gateway_integration.lambda
  ]
}
"""

def generate_python_terraform(md_data: Dict[str, Any]) -> str:
    """Generate Terraform for Python applications"""
    return """# Terraform configuration for Python Application
provider "aws" {
  region = var.region
}

# Lambda function for the Python API
resource "aws_lambda_function" "api" {
  function_name    = "${var.app_name}-${var.environment}"
  handler          = "app.lambda_handler"
  runtime          = "python3.9"
  filename         = "${path.module}/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda.zip")
  role             = aws_iam_role.lambda_role.arn
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory_size
  
  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }
}

# API Gateway
resource "aws_api_gateway_rest_api" "api" {
  name        = "${var.app_name}-${var.environment}-api"
  description = "API Gateway for ${var.app_name}"
}

# Set up a proxy resource to catch all requests
resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "{proxy+}"
}
"""

def generate_generic_terraform(md_data: Dict[str, Any]) -> str:
    """Generate a generic Terraform configuration"""
    return """# Generic Terraform configuration
provider "aws" {
  region = var.region
}

# S3 bucket for application storage
resource "aws_s3_bucket" "app_bucket" {
  bucket = "${var.app_name}-${var.environment}-${var.region}"
  
  tags = {
    Name        = "${var.app_name}"
    Environment = var.environment
  }
}

# EC2 instance for application
resource "aws_instance" "app_server" {
  ami           = var.ami_id
  instance_type = var.instance_type
  key_name      = var.key_name
  
  tags = {
    Name        = "${var.app_name}-server"
    Environment = var.environment
  }
}

# Security group for EC2 instance
resource "aws_security_group" "app_sg" {
  name        = "${var.app_name}-sg"
  description = "Security group for ${var.app_name}"
  
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
}
"""

def generate_variables_tf(md_data: Dict[str, Any]) -> str:
    """Generate variables.tf file"""
    return """# Variables for Terraform configuration

variable "region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "app_name" {
  description = "Name of the application"
  type        = string
  default     = "app"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "mongo_uri" {
  description = "MongoDB connection string"
  type        = string
  default     = "mongodb://localhost:27017/app"
  sensitive   = true
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "ami_id" {
  description = "AMI ID for EC2 instance"
  type        = string
  default     = "ami-0c55b159cbfafe1f0"  # Amazon Linux 2 AMI (HVM), SSD Volume Type
}

variable "key_name" {
  description = "SSH key pair name"
  type        = string
  default     = null
}
"""

def generate_outputs_tf(md_data: Dict[str, Any]) -> str:
    """Generate outputs.tf file"""
    return """# Outputs for Terraform configuration

output "api_url" {
  description = "URL of the API Gateway (if deployed)"
  value       = try(aws_api_gateway_deployment.api.invoke_url, "N/A")
}

output "lambda_function_name" {
  description = "Name of the Lambda function (if deployed)"
  value       = try(aws_lambda_function.api.function_name, "N/A")
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket (if deployed)"
  value       = try(aws_s3_bucket.app_bucket.id, "N/A")
}

output "ec2_instance_ip" {
  description = "IP address of the EC2 instance (if deployed)"
  value       = try(aws_instance.app_server.public_ip, "N/A")
}
"""

def generate_tfvars(md_data: Dict[str, Any]) -> str:
    """Generate terraform.tfvars file"""
    app_name = "app"
    language = md_data.get("language", "").lower()
    framework = md_data.get("framework", "").lower()
    
    if language and framework:
        app_name = f"{language.replace('.', '-').replace('/', '-')}-{framework}-app"
    
    mongo_uri = "mongodb://localhost:27017/db"
    if md_data.get("database", "").lower() == "mongodb":
        mongo_uri = "mongodb://localhost:27017/db"
    
    return f"""region = "us-east-1"
app_name = "{app_name}"
environment = "dev"
lambda_timeout = 30
lambda_memory_size = 512
mongo_uri = "{mongo_uri}"
"""

def generate_readme(md_data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """Generate README.md file with infrastructure recommendations and instructions"""
    # Get the list of AWS services
    services = analysis.get("services", [])
    services_section = "\n".join([f"- {service}" for service in services])
    
    # Get the recommendations
    recommendations = analysis.get("recommendations", [])
    recommendations_section = "\n".join([f"- {rec}" for rec in recommendations])
    
    # Get the cost estimation
    cost_estimation = analysis.get("cost_estimation", "")
    
    # Include the full AI response if available
    ai_response = analysis.get("ai_response", "")
    
    # Extract human-readable recommendations from AI response if available
    ai_recommendations = ""
    if ai_response and "RECOMMENDATIONS:" in ai_response:
        try:
            # Extract the RECOMMENDATIONS section
            rec_section = ai_response.split("RECOMMENDATIONS:")[1].split("COST_ESTIMATION:")[0].strip() if "COST_ESTIMATION:" in ai_response else ai_response.split("RECOMMENDATIONS:")[1].split("TERRAFORM_TEMPLATE:")[0].strip()
            ai_recommendations = rec_section
        except Exception:
            # If there's an error extracting, use what we have
            ai_recommendations = ""
    
    # Extract recommended services without code
    ai_services = ""
    if ai_response and "RECOMMENDED_SERVICES:" in ai_response:
        try:
            # Extract the RECOMMENDED_SERVICES section
            services_section = ai_response.split("RECOMMENDED_SERVICES:")[1].split("RECOMMENDATIONS:")[0].strip()
            ai_services = services_section
        except Exception:
            ai_services = ""
    
    # Extract cost estimation from AI response if available
    ai_cost_estimation = ""
    if ai_response and "COST_ESTIMATION:" in ai_response:
        try:
            # Extract the COST_ESTIMATION section
            cost_section = ai_response.split("COST_ESTIMATION:")[1].split("TERRAFORM_TEMPLATE:")[0].strip()
            ai_cost_estimation = cost_section
        except Exception:
            ai_cost_estimation = ""
    
    readme = f"""# Infrastructure Deployment Recommendations

## Executive Summary

This infrastructure plan was generated by Inframate based on analyzing your application's requirements and codebase structure.
"""

    # Add AI recommended services if available, otherwise use the parsed ones
    if ai_services:
        readme += f"""
### Recommended AWS Services:

{ai_services}
"""
    else:
        readme += f"""
### Recommended AWS Services:

{services_section}
"""

    # Add AI recommendations if available
    if ai_recommendations:
        # Clean up the recommendations to remove any code blocks
        cleaned_recommendations = []
        lines = ai_recommendations.split('\n')
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
                
            if not in_code_block and line.strip():
                cleaned_recommendations.append(line)
        
        cleaned_text = '\n'.join(cleaned_recommendations)
        
        # Only add if we have non-empty recommendations after cleaning
        if cleaned_text.strip():
            readme += f"""
## Detailed Recommendations

{cleaned_text}
"""
    # Otherwise use the basic recommendations
    else:
        readme += f"""
## Recommendations

{recommendations_section}
"""

    # Add cost estimation section if available
    if ai_cost_estimation:
        # Clean up the cost estimation to remove any code blocks
        cleaned_cost = []
        lines = ai_cost_estimation.split('\n')
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
                
            if not in_code_block and line.strip():
                cleaned_cost.append(line)
        
        cleaned_cost_text = '\n'.join(cleaned_cost)
        
        # Only add if we have non-empty cost estimation after cleaning
        if cleaned_cost_text.strip():
            readme += f"""
## Estimated Monthly Costs

{cleaned_cost_text}

*Note: These cost estimates are approximate and may vary based on usage patterns, region, and AWS pricing changes.*
"""
    elif cost_estimation:
        readme += f"""
## Estimated Monthly Costs

{cost_estimation}

*Note: These cost estimates are approximate and may vary based on usage patterns, region, and AWS pricing changes.*
"""

    # Add deployment instructions
    readme += f"""
## Deployment Instructions

1. **Prerequisites**:
   - AWS CLI configured with appropriate credentials
   - Terraform installed (v1.0.0+)

2. **Configuration**:
   - Update variables in `terraform.tfvars` to match your requirements
   - Review the Terraform files to ensure they meet your needs

3. **Deployment**:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

4. **Cleanup**:
   ```bash
   terraform destroy
   ```

## Notes

- The Terraform files have been generated in the `terraform/` directory
- The configuration is based on the application requirements specified in `inframate.md`
- You may need to customize the Terraform files for your specific needs
"""
    
    return readme

def generate_terraform_files(repo_path: str, analysis: Dict[str, Any], md_data: Dict[str, Any]) -> str:
    """Generate Terraform files in the repository"""
    print("Generating Terraform files...")
    
    # Create terraform directory if it doesn't exist
    tf_dir = os.path.join(repo_path, 'terraform')
    os.makedirs(tf_dir, exist_ok=True)
    
    # Generate main.tf
    terraform_template = ""
    if "terraform_template" in analysis and analysis["terraform_template"]:
        terraform_template = analysis["terraform_template"]
    else:
        print("No Terraform template in analysis, generating basic template...")
        # Use local templates based on language/framework
        terraform_template = generate_terraform_template(md_data, analysis.get("services", []))
    
    # Create main.tf
    with open(os.path.join(tf_dir, 'main.tf'), 'w') as f:
        f.write(terraform_template)
    
    # Create variables.tf
    variables_tf = generate_variables_tf(md_data)
    with open(os.path.join(tf_dir, 'variables.tf'), 'w') as f:
        f.write(variables_tf)
    
    # Create outputs.tf
    outputs_tf = generate_outputs_tf(md_data)
    with open(os.path.join(tf_dir, 'outputs.tf'), 'w') as f:
        f.write(outputs_tf)
    
    # Create terraform.tfvars
    tfvars = generate_tfvars(md_data)
    with open(os.path.join(tf_dir, 'terraform.tfvars'), 'w') as f:
        f.write(tfvars)
    
    # Create README.md
    readme = generate_readme(md_data, analysis)
    with open(os.path.join(tf_dir, 'README.md'), 'w') as f:
        f.write(readme)
    
    print(f"Terraform files created in {tf_dir}")
    return tf_dir

def main(argv=None):
    """Main entry point for Inframate"""
    if argv is None:
        argv = sys.argv
    
    if len(argv) != 2:
        print("Usage: python -m inframate.flow <repository_path>")
        sys.exit(1)
    
    repo_path = argv[1]
    
    try:
        # Read repository information
        repo_info = read_inframate_file(repo_path)
        
        # Add repo path to the info
        repo_info['repo_path'] = repo_path
        
        # Analyze repository structure
        repo_analysis = analyze_repository(repo_path)
        repo_info.update(repo_analysis)
        
        # Get AI analysis
        try:
            analysis_result = analyze_with_ai(repo_info)
        except Exception as e:
            print(f"AI analysis failed: {str(e)}")
            print("Falling back to basic analysis...")
            analysis_result = fallback_analyze(repo_info)
        
        # Generate Terraform files
        terraform_dir = generate_terraform_files(repo_path, analysis_result, repo_info)
        
        print("Inframate analysis complete!")
        print(f"Terraform files generated in: {terraform_dir}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 