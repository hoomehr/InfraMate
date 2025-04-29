"""
AI-powered repository analyzer using Google Gemini
"""
import os
import json
import yaml
import google.generativeai as genai
from dotenv import load_dotenv
from inframate.utils.rag import RAGManager
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

# Load environment variables
load_dotenv()

# Get API key from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize RAG manager
rag_manager = RAGManager()

def analyze_directory_structure(repo_path: str) -> Dict[str, Any]:
    """
    Analyze the directory structure of the repository
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary containing information about the directory structure
    """
    repo_dir = Path(repo_path)
    
    # Count files by extension
    file_extensions = {}
    file_count = 0
    dir_count = 0
    
    for root, dirs, files in os.walk(repo_dir):
        # Skip .git and other hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        rel_path = os.path.relpath(root, repo_path)
        if rel_path == '.':
            rel_path = ''
        
        for file in files:
            if file.startswith('.'):
                continue
                
            file_count += 1
            _, ext = os.path.splitext(file)
            if ext:
                ext = ext.lower()
                file_extensions[ext] = file_extensions.get(ext, 0) + 1
        
        dir_count += len(dirs)
    
    # Get top directories
    top_dirs = []
    for item in os.listdir(repo_dir):
        item_path = repo_dir / item
        if item_path.is_dir() and not item.startswith('.'):
            top_dirs.append(item)
    
    # Check for common project files
    has_docker = os.path.exists(repo_dir / 'Dockerfile') or os.path.exists(repo_dir / 'docker-compose.yml')
    has_kubernetes = any(os.path.exists(repo_dir / item) for item in ['k8s', 'kubernetes', 'helm'])
    has_ci = any(os.path.exists(repo_dir / item) for item in ['.github', '.gitlab-ci.yml', '.circleci'])
    
    return {
        'file_count': file_count,
        'dir_count': dir_count,
        'file_extensions': file_extensions,
        'top_directories': top_dirs,
        'has_docker': has_docker,
        'has_kubernetes': has_kubernetes,
        'has_ci': has_ci
    }

def analyze_with_ai(repo_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze repository info using Gemini API
    
    Args:
        repo_info: Dictionary containing information about the repository
        
    Returns:
        Dictionary containing analysis results
    """
    # Get Gemini API key from environment
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Warning: GEMINI_API_KEY not set. Using fallback analysis.")
        return fallback_analyze(repo_info)
    
    # Add directory structure analysis if it's not already there
    if 'directory_structure' not in repo_info and 'repo_path' in repo_info:
        try:
            repo_info['directory_structure'] = analyze_directory_structure(repo_info['repo_path'])
        except Exception as e:
            print(f"Warning: Failed to analyze directory structure: {e}")
    
    # Build the prompt for Gemini API
    language = repo_info.get('language', 'Unknown')
    framework = repo_info.get('framework', 'Unknown')
    database = repo_info.get('database', 'None')
    requirements = repo_info.get('requirements', '')
    description = repo_info.get('description', '')
    
    dir_structure = "Not available"
    if 'directory_structure' in repo_info:
        dir_structure = json.dumps(repo_info['directory_structure'], indent=2)
    
    prompt = f"""
You are an expert DevOps engineer. Analyze the following application and provide infrastructure recommendations and Terraform configuration.

APPLICATION DETAILS:
- Language: {language}
- Framework: {framework}
- Database: {database}
- Requirements: {requirements}
- Description: {description}

DIRECTORY STRUCTURE:
{dir_structure}

Based on this information, please provide:
1. A list of recommended AWS services for deployment (comma-separated)
2. Infrastructure recommendations (bullet points)
3. A complete Terraform template for deploying this application to AWS

Format your response with clear sections:
RECOMMENDED_SERVICES: (comma-separated list of AWS services)
RECOMMENDATIONS: (bullet points for infrastructure recommendations)
TERRAFORM_TEMPLATE: (complete, production-ready Terraform code)
"""
    
    try:
        # Call Gemini API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            print(f"Warning: Gemini API request failed with status {response.status_code}")
            return fallback_analyze(repo_info)
        
        response_data = response.json()
        
        # Extract the text from the response
        ai_response = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        # Parse the response to extract the services, recommendations, and Terraform template
        services = []
        recommendations = []
        terraform_template = ""
        
        if "RECOMMENDED_SERVICES:" in ai_response:
            services_section = ai_response.split("RECOMMENDED_SERVICES:")[1].split("RECOMMENDATIONS:")[0].strip()
            services = [service.strip() for service in services_section.split(",")]
        
        if "RECOMMENDATIONS:" in ai_response:
            recommendations_section = ai_response.split("RECOMMENDATIONS:")[1].split("TERRAFORM_TEMPLATE:")[0].strip()
            recommendations = [rec.strip().lstrip("- ") for rec in recommendations_section.split("\n") if rec.strip()]
        
        if "TERRAFORM_TEMPLATE:" in ai_response:
            template_section = ai_response.split("TERRAFORM_TEMPLATE:")[1].strip()
            # Check if the template is in a code block
            if "```" in template_section:
                # Extract the template from within the code block
                parts = template_section.split("```")
                if len(parts) >= 3:  # There should be at least 3 parts: before, content, after
                    terraform_template = parts[1].strip()
                    if terraform_template.startswith("terraform") or terraform_template.startswith("hcl"):
                        terraform_template = terraform_template.split("\n", 1)[1]  # Remove the language identifier
            else:
                # Just use the raw template
                terraform_template = template_section
        
        return {
            "services": services,
            "recommendations": recommendations,
            "terraform_template": terraform_template,
            "ai_response": ai_response  # Store the full response for the README
        }
    
    except Exception as e:
        print(f"Warning: Failed to analyze with Gemini API: {e}")
        return fallback_analyze(repo_info)

def fallback_analyze(repo_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback analysis when AI analysis fails
    
    Args:
        repo_info: Dictionary containing information about the repository
        
    Returns:
        Dictionary containing analysis results
    """
    services = []
    recommendations = []
    
    # Determine services based on language and framework
    language = repo_info.get('language', '').lower()
    framework = repo_info.get('framework', '').lower()
    database = repo_info.get('database', '').lower()
    
    # Analyze for Node.js
    if 'node' in language or 'javascript' in language or 'typescript' in language:
        services.extend(["Lambda", "API Gateway", "CloudWatch"])
        recommendations.append("Use serverless architecture with Lambda and API Gateway for Node.js applications")
        
        if 'express' in framework:
            services.append("Lambda")
            recommendations.append("Consider using AWS Lambda with Express.js adapter")
        
        if 'react' in framework or 'vue' in framework or 'angular' in framework:
            services.extend(["S3", "CloudFront"])
            recommendations.append("Host frontend on S3 with CloudFront for global CDN")
    
    # Analyze for Python
    elif 'python' in language:
        services.extend(["Lambda", "API Gateway", "CloudWatch"])
        recommendations.append("Use AWS Lambda for Python applications")
        
        if 'django' in framework or 'flask' in framework:
            services.extend(["Elastic Beanstalk", "RDS"])
            recommendations.append("Consider Elastic Beanstalk for Django or Flask applications")
    
    # Analyze for Java
    elif 'java' in language:
        services.extend(["EC2", "Auto Scaling", "Elastic Load Balancer"])
        recommendations.append("Use EC2 with Auto Scaling for Java applications")
        
        if 'spring' in framework:
            services.extend(["Elastic Beanstalk", "RDS"])
            recommendations.append("Consider Elastic Beanstalk for Spring applications")
    
    # Database recommendations
    if 'mongodb' in database:
        services.append("DocumentDB")
        recommendations.append("Use Amazon DocumentDB for MongoDB compatibility")
    elif 'mysql' in database or 'postgresql' in database:
        services.append("RDS")
        recommendations.append("Use Amazon RDS for relational database needs")
    
    # Add generic recommendations
    recommendations.extend([
        "Use Infrastructure as Code (IaC) with Terraform for reproducible deployments",
        "Implement proper logging and monitoring with CloudWatch",
        "Set up proper IAM roles and policies for security"
    ])
    
    # Generate a terraform template
    terraform_template = generate_terraform_template(repo_info, services)
    
    # Add the fallback information for the README
    fallback_note = """
NOTE: This analysis was performed using Inframate's built-in rules since the AI analysis was unavailable.
For more accurate and detailed recommendations, please ensure the GEMINI_API_KEY is properly configured.
"""
    
    return {
        "services": list(set(services)),  # Remove duplicates
        "recommendations": recommendations,
        "terraform_template": terraform_template,
        "ai_response": fallback_note  # Add note for README
    }

def generate_terraform_template(repo_info: Dict[str, Any], services: List[str]) -> str:
    """
    Generate a basic Terraform template based on detected services
    
    Args:
        repo_info: Repository information
        services: List of detected services
        
    Returns:
        String containing Terraform template
    """
    template = """# Terraform configuration generated by Inframate
provider "aws" {
  region = var.region
}

"""
    
    # Add resources based on services
    if "Lambda" in services:
        template += """
resource "aws_lambda_function" "app" {
  function_name    = "${var.app_name}-${var.environment}"
  handler          = "index.handler"
  runtime          = "nodejs18.x"
  filename         = "${path.module}/deployment.zip"
  source_code_hash = filebase64sha256("${path.module}/deployment.zip")
  role             = aws_iam_role.lambda_role.arn
  memory_size      = 512
  timeout          = 30
  
  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "${var.app_name}-lambda-role"
  
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

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
"""
    
    if "API Gateway" in services:
        template += """
resource "aws_api_gateway_rest_api" "api" {
  name        = "${var.app_name}-api"
  description = "API for ${var.app_name}"
}

resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization_type = "NONE"
}

resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy.http_method
  
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.app.invoke_arn
}

resource "aws_api_gateway_deployment" "api" {
  depends_on = [
    aws_api_gateway_integration.lambda
  ]
  
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = var.environment
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.app.function_name
  principal     = "apigateway.amazonaws.com"
  
  source_arn = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}
"""
    
    if "S3" in services:
        template += """
resource "aws_s3_bucket" "frontend" {
  bucket = "${var.app_name}-${var.environment}-frontend"
  
  tags = {
    Name        = "${var.app_name}-frontend"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  
  index_document {
    suffix = "index.html"
  }
  
  error_document {
    key = "error.html"
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = ["s3:GetObject"]
        Effect    = "Allow"
        Resource  = "${aws_s3_bucket.frontend.arn}/*"
        Principal = "*"
      }
    ]
  })
}
"""
    
    if "CloudFront" in services:
        template += """
resource "aws_cloudfront_distribution" "frontend" {
  origin {
    domain_name = aws_s3_bucket_website_configuration.frontend.website_endpoint
    origin_id   = "S3-${aws_s3_bucket.frontend.bucket}"
    
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1", "TLSv1.1", "TLSv1.2"]
    }
  }
  
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.frontend.bucket}"
    
    forwarded_values {
      query_string = false
      
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }
  
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
"""
    
    if "RDS" in services:
        template += """
resource "aws_db_instance" "database" {
  allocated_storage    = 20
  storage_type         = "gp2"
  engine               = "mysql"
  engine_version       = "8.0"
  instance_class       = "db.t3.micro"
  identifier           = "${var.app_name}-${var.environment}"
  username             = "admin"
  password             = var.db_password
  parameter_group_name = "default.mysql8.0"
  skip_final_snapshot  = true
  publicly_accessible  = false
  
  tags = {
    Name        = "${var.app_name}-database"
    Environment = var.environment
  }
}
"""
    
    if "Auto Scaling" in services:
        template += """
resource "aws_launch_configuration" "app" {
  name_prefix     = "${var.app_name}-"
  image_id        = var.ami_id
  instance_type   = var.instance_type
  security_groups = [aws_security_group.app.id]
  
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "app" {
  name                 = "${var.app_name}-asg"
  launch_configuration = aws_launch_configuration.app.name
  min_size             = 1
  max_size             = 3
  desired_capacity     = 2
  vpc_zone_identifier  = var.subnet_ids
  target_group_arns    = [aws_lb_target_group.app.arn]
  
  tag {
    key                 = "Name"
    value               = "${var.app_name}-instance"
    propagate_at_launch = true
  }
  
  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }
}

resource "aws_autoscaling_policy" "scale_up" {
  name                   = "${var.app_name}-scale-up"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  autoscaling_group_name = aws_autoscaling_group.app.name
}

resource "aws_autoscaling_policy" "scale_down" {
  name                   = "${var.app_name}-scale-down"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  autoscaling_group_name = aws_autoscaling_group.app.name
}
"""
    
    # Add output section
    template += """
output "app_url" {
  description = "URL to access the application"
  value       = try(aws_api_gateway_deployment.api.invoke_url, 
            try(aws_cloudfront_distribution.frontend.domain_name, 
            try(aws_lb.app.dns_name, "Not available")))
}
"""
    
    return template 