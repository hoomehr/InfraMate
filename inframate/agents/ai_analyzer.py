"""
AI-powered repository analyzer using Google Gemini
"""
import os
import json
import yaml
import google.generativeai as genai
from dotenv import load_dotenv
from inframate.utils.rag import RAGManager

# Load environment variables
load_dotenv()

# Get API key from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize RAG manager
rag_manager = RAGManager()

def analyze_with_ai(repo_path, data):
    """
    Use AI to analyze repository and generate infrastructure recommendations
    
    Args:
        repo_path (str): Path to the repository
        data (dict): Data from previous analysis steps
        
    Returns:
        dict: AI analysis results with Terraform template
    """
    if not GOOGLE_API_KEY:
        return fallback_analyze(repo_path, data)
    
    try:
        # Configure the Gemini API
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # Get Gemini model
        model = genai.GenerativeModel("gemini-1.5-pro")
        
        # Prepare the prompt with repository information
        prompt = create_analysis_prompt(repo_path, data)
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Extract the analysis from the response
        analysis_text = response.text
        
        # Try to parse the JSON from the response
        try:
            # Extract JSON if it's wrapped in ```json ... ``` format
            if "```json" in analysis_text and "```" in analysis_text:
                json_str = analysis_text.split("```json")[1].split("```")[0].strip()
                analysis = json.loads(json_str)
            else:
                # Look for any JSON block
                start_idx = analysis_text.find('{')
                end_idx = analysis_text.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = analysis_text[start_idx:end_idx]
                    analysis = json.loads(json_str)
                else:
                    # Create a structured response from the text
                    analysis = {
                        "languages": extract_languages(analysis_text),
                        "services": extract_services(analysis_text),
                        "recommendations": extract_recommendations(analysis_text),
                        "resources": [],
                        "terraform_template": extract_terraform_template(analysis_text),
                        "estimatedCost": "Unknown",
                        "warnings": []
                    }
        except json.JSONDecodeError:
            # If JSON parsing fails, create a structured response from the text
            analysis = {
                "languages": extract_languages(analysis_text),
                "services": extract_services(analysis_text),
                "recommendations": extract_recommendations(analysis_text),
                "resources": [],
                "terraform_template": extract_terraform_template(analysis_text),
                "estimatedCost": "Unknown",
                "warnings": []
            }
        
        # If we don't have a Terraform template yet, generate one
        if not analysis.get("terraform_template") or analysis["terraform_template"] == "":
            terraform_template = generate_terraform_template(repo_path, data, analysis)
            analysis["terraform_template"] = terraform_template
        
        return analysis
    
    except Exception as e:
        if data.get("verbose"):
            print(f"Error using Gemini for analysis: {str(e)}")
        return fallback_analyze(repo_path, data)

def create_analysis_prompt(repo_path, data):
    """
    Create a prompt for the AI based on repository data
    
    Args:
        repo_path (str): Path to the repository
        data (dict): Repository analysis data
        
    Returns:
        str: Prompt for AI analysis
    """
    prompt = f"""
Please analyze this repository for AWS deployment requirements:

Repository Path: {repo_path}

"""
    
    # Add readme content if available
    if data.get("readme"):
        # Truncate readme if it's too long
        readme = data["readme"][:4000] + "..." if len(data["readme"]) > 4000 else data["readme"]
        prompt += f"README.md excerpt:\n{readme}\n\n"
    
    # Add framework information
    if data.get("framework"):
        framework = data["framework"]
        prompt += "Detected frameworks:\n"
        prompt += f"- Language: {framework.get('language') or 'Unknown'}\n"
        
        if framework.get("frontend"):
            prompt += f"- Frontend: {framework['frontend']}\n"
        if framework.get("backend"):
            prompt += f"- Backend: {framework['backend']}\n"
        if framework.get("database"):
            prompt += f"- Database: {framework['database']}\n"
        if framework.get("other"):
            prompt += f"- Other: {', '.join(framework['other'])}\n"
        prompt += "\n"
    
    # Add infrastructure information
    if data.get("infrastructure"):
        infra = data["infrastructure"]
        prompt += "Detected infrastructure:\n"
        
        if infra["type"]:
            prompt += f"- Type: {infra['type']}\n"
        
        # Add cloud provider information
        for provider in ["aws", "azure", "gcp"]:
            if infra[provider]["detected"]:
                services = infra[provider]["services"]
                services_str = ", ".join(services) if services else "Unknown"
                prompt += f"- {provider.upper()}: Detected with services: {services_str}\n"
        
        # Add other infrastructure information
        infra_types = []
        if infra["cloudformation"]:
            infra_types.append("CloudFormation")
        if infra["terraform"]:
            infra_types.append("Terraform")
        if infra["kubernetes"]:
            infra_types.append("Kubernetes")
        if infra["docker"]:
            infra_types.append("Docker")
        
        if infra_types:
            prompt += f"- Infrastructure tools: {', '.join(infra_types)}\n"
        
        prompt += "\n"
    
    # Add Inframate configuration if available
    if data.get("config") and data["config"]:
        prompt += f"Inframate configuration:\n{yaml.dump(data['config'])}\n\n"
    
    prompt += """
Based on this information, please provide a detailed analysis with the following:

1. Detected programming languages
2. AWS services that would be needed for deployment
3. Specific deployment recommendations and infrastructure needed
4. A complete Terraform template for deploying the required AWS infrastructure
5. Estimated monthly cost
6. Any warnings or potential issues

The Terraform template should be complete and ready to use, with all necessary resources, variables, outputs, and providers. 
Put the terraform code inside ```terraform and ``` tags.

Return your analysis as a JSON object with these keys:
languages, services, recommendations, terraform_template, estimatedCost, warnings
"""
    
    return prompt

def generate_terraform_template(repo_path, data, analysis):
    """
    Generate a Terraform template using RAG and Gemini
    
    Args:
        repo_path (str): Path to the repository
        data (dict): Repository analysis data
        analysis (dict): Analysis results
        
    Returns:
        str: Terraform template
    """
    if not GOOGLE_API_KEY:
        return "# Terraform template generation requires Google API key"
    
    try:
        # Configure the Gemini API if not already configured
        if not genai._configured:
            genai.configure(api_key=GOOGLE_API_KEY)
        
        # Get Gemini model
        model = genai.GenerativeModel("gemini-1.5-pro")
        
        # Create query for RAG
        query = f"Infrastructure for {data.get('framework', {}).get('language', 'unknown')} "
        
        if data.get('framework', {}).get('frontend'):
            query += f"with {data['framework']['frontend']} frontend "
        
        if data.get('framework', {}).get('backend'):
            query += f"and {data['framework']['backend']} backend "
        
        if len(analysis.get('services', [])) > 0:
            query += f"using AWS {', '.join(analysis['services'])} "
        
        # Retrieve similar templates
        similar_templates = rag_manager.retrieve_similar_templates(query)
        
        # Extract template types and build context
        template_types = []
        context = "Here are some relevant Terraform templates for reference:\n\n"
        
        for template in similar_templates:
            template_type = template['metadata']['type']
            if template_type not in template_types:
                template_types.append(template_type)
                full_template = rag_manager.get_template_by_name(template_type)
                if full_template:
                    context += f"Terraform template for {template_type}:\n```terraform\n{full_template[:1500]}...\n```\n\n"
        
        # Create prompt for Terraform template generation
        prompt = f"""
I need a complete Terraform template for an AWS infrastructure deployment based on the following repository analysis:

Repository Path: {repo_path}

Language: {data.get('framework', {}).get('language', 'Unknown')}
Frontend: {data.get('framework', {}).get('frontend', 'None')}
Backend: {data.get('framework', {}).get('backend', 'None')}
Database: {data.get('framework', {}).get('database', 'None')}

Detected AWS services: {', '.join(analysis.get('services', ['None']))}

Recommendations:
{chr(10).join(['- ' + rec for rec in analysis.get('recommendations', ['No recommendations'])])}

{context}

Please generate a complete and well-structured Terraform template that can be used to deploy the infrastructure for this repository.
Include all necessary providers, variables, resources, and outputs.
Make the template modular and follow Terraform best practices.
The template should be ready to use with minimal modifications.
"""
        
        # Generate response
        response = model.generate_content(prompt)
        terraform_template = response.text
        
        # Extract the Terraform template from the response
        return extract_terraform_template(terraform_template)
    
    except Exception as e:
        if data.get("verbose"):
            print(f"Error generating Terraform template: {str(e)}")
        return "# Failed to generate Terraform template\n# Please check your Google API key and try again"

def extract_terraform_template(text):
    """Extract Terraform template from AI response text"""
    # Look for Terraform code blocks
    if "```terraform" in text and "```" in text:
        start = text.find("```terraform") + len("```terraform")
        end = text.find("```", start)
        if end > start:
            return text[start:end].strip()
    
    # Look for HCL code blocks
    if "```hcl" in text and "```" in text:
        start = text.find("```hcl") + len("```hcl")
        end = text.find("```", start)
        if end > start:
            return text[start:end].strip()
    
    # Look for generic code blocks that might contain Terraform
    if "```" in text:
        parts = text.split("```")
        for i in range(1, len(parts), 2):
            if "provider" in parts[i] and "aws" in parts[i] and "resource" in parts[i]:
                return parts[i].strip()
    
    # If we can't find a code block, look for sections that might contain Terraform code
    if "provider \"aws\"" in text:
        # Try to extract a block of text that looks like Terraform
        lines = text.split("\n")
        start_idx = -1
        end_idx = -1
        
        for i, line in enumerate(lines):
            if "provider \"aws\"" in line and start_idx == -1:
                start_idx = i
            if start_idx != -1 and end_idx == -1 and line.strip() == "}" and i > start_idx + 5:
                # Look ahead to see if this is the end of the Terraform code
                if i + 1 < len(lines) and (lines[i+1].strip() == "" or not lines[i+1].strip().startswith("#")):
                    end_idx = i
        
        if start_idx != -1 and end_idx != -1:
            return "\n".join(lines[start_idx:end_idx+1])
    
    return ""

def extract_languages(text):
    """Extract programming languages from AI response text"""
    common_languages = ["javascript", "python", "java", "ruby", "go", "rust", 
                       "typescript", "php", "c#", "c++", "html", "css", 
                       "shell", "bash", "node.js", "nodejs"]
    
    languages = []
    for lang in common_languages:
        if lang.lower() in text.lower():
            # Normalize Node.js variants
            if lang.lower() in ["node.js", "nodejs"]:
                if "Node.js" not in languages and "NodeJS" not in languages:
                    languages.append("Node.js")
            else:
                # Capitalize properly
                if lang.lower() == "javascript":
                    languages.append("JavaScript")
                elif lang.lower() == "typescript":
                    languages.append("TypeScript")
                elif lang.lower() == "c#":
                    languages.append("C#")
                elif lang.lower() == "c++":
                    languages.append("C++")
                elif lang.lower() == "php":
                    languages.append("PHP")
                elif lang.lower() == "html":
                    languages.append("HTML")
                elif lang.lower() == "css":
                    languages.append("CSS")
                else:
                    languages.append(lang.capitalize())
    
    return languages

def extract_services(text):
    """Extract AWS services from AI response text"""
    common_aws_services = [
        "EC2", "Lambda", "S3", "DynamoDB", "RDS", "API Gateway", 
        "CloudFront", "Route 53", "SQS", "SNS", "ECS", "EKS", 
        "Fargate", "CloudFormation", "ElastiCache", "CodeBuild",
        "CodePipeline", "Amplify", "AppSync", "Cognito"
    ]
    
    services = []
    for service in common_aws_services:
        service_variations = [
            service, 
            service.lower(), 
            service.replace(" ", ""),
            service.lower().replace(" ", "")
        ]
        
        for variation in service_variations:
            if variation in text:
                if service not in services:
                    services.append(service)
                break
    
    return services

def extract_recommendations(text):
    """Extract deployment recommendations from AI response text"""
    # Split text into paragraphs and lines
    paragraphs = text.split("\n\n")
    lines = text.split("\n")
    
    recommendations = []
    
    # Look for lists or paragraphs containing recommendations
    for item in lines:
        item = item.strip()
        if item.startswith("- ") or item.startswith("* "):
            # Extract list items
            recommendation = item[2:].strip()
            if len(recommendation) > 10 and recommendation not in recommendations:
                recommendations.append(recommendation)
    
    # If we couldn't find specific recommendations, extract sentences containing key phrases
    if not recommendations:
        recommendation_phrases = [
            "recommend", "suggest", "deploy", "should use", "could use", 
            "best practice", "optimal", "ideal", "consider"
        ]
        
        for paragraph in paragraphs:
            for phrase in recommendation_phrases:
                if phrase in paragraph.lower():
                    # Add the entire paragraph as a recommendation
                    if paragraph.strip() not in recommendations and len(paragraph.strip()) > 10:
                        recommendations.append(paragraph.strip())
                        break
    
    # Limit to 5 recommendations maximum
    return recommendations[:5]

def fallback_analyze(repo_path, data):
    """
    Fallback analysis when AI is unavailable
    
    Args:
        repo_path (str): Path to the repository
        data (dict): Repository analysis data
        
    Returns:
        dict: Basic analysis results with simple Terraform template
    """
    if data.get("verbose"):
        print("Using fallback analysis without AI")
    
    framework = data.get("framework", {})
    infrastructure = data.get("infrastructure", {})
    
    # Determine language
    language = None
    if framework and framework.get("language"):
        language = framework["language"]
    
    # Basic recommendations based on detected frameworks
    recommendations = []
    
    if language == "JavaScript/Node.js":
        if framework.get("backend") in ["Express", "Koa", "Fastify", "NestJS"]:
            recommendations.append("Deploy as an AWS Lambda function with API Gateway for the Node.js backend")
        elif "Serverless Framework" in framework.get("other", []):
            recommendations.append("Use the existing Serverless Framework configuration to deploy to AWS Lambda")
        else:
            recommendations.append("Deploy the Node.js application using AWS Elastic Beanstalk")
        
        if framework.get("frontend") == "React":
            recommendations.append("Host the React frontend on AWS S3 with CloudFront for caching")
    
    elif language == "Python":
        if framework.get("backend") == "Django":
            recommendations.append("Deploy Django application on AWS Elastic Beanstalk with RDS for database")
        elif framework.get("backend") == "Flask":
            recommendations.append("Deploy Flask application as AWS Lambda functions with API Gateway")
        else:
            recommendations.append("Deploy Python application on AWS Lambda for serverless execution")
    
    # Add database recommendations
    if framework.get("database"):
        if "MongoDB" in framework.get("database"):
            recommendations.append("Use MongoDB Atlas or DocumentDB for MongoDB database")
        elif "SQL" in framework.get("database") or "Postgres" in framework.get("database"):
            recommendations.append("Use AWS RDS for SQL database needs")
    
    # Add recommendations based on detected infrastructure
    if infrastructure.get("docker"):
        recommendations.append("Use AWS ECS or EKS to deploy the Docker containers")
    
    if infrastructure.get("kubernetes"):
        recommendations.append("Use AWS EKS for Kubernetes cluster management")
    
    # Add default recommendation if none were added
    if not recommendations:
        recommendations.append("Deploy on AWS Elastic Beanstalk for a managed platform experience")
        recommendations.append("Consider using AWS Lambda for serverless compute if applicable")
    
    # Detect services based on recommendations and infrastructure
    services = []
    if "Lambda" in " ".join(recommendations):
        services.append("Lambda")
    if "API Gateway" in " ".join(recommendations):
        services.append("API Gateway")
    if "S3" in " ".join(recommendations):
        services.append("S3")
    if "CloudFront" in " ".join(recommendations):
        services.append("CloudFront")
    if "Elastic Beanstalk" in " ".join(recommendations):
        services.append("Elastic Beanstalk")
    if "ECS" in " ".join(recommendations) or "EKS" in " ".join(recommendations):
        services.append("ECS" if "ECS" in " ".join(recommendations) else "EKS")
    if "RDS" in " ".join(recommendations):
        services.append("RDS")
    
    # Detect languages based on framework
    languages = []
    if language == "JavaScript/Node.js":
        languages.extend(["JavaScript", "Node.js"])
        if framework.get("frontend") == "React":
            languages.extend(["JSX", "HTML", "CSS"])
    elif language == "Python":
        languages.append("Python")
    
    # Generate a simple Terraform template based on detected services
    terraform_template = generate_fallback_terraform_template(services, language, framework)
    
    return {
        "languages": languages,
        "services": services,
        "recommendations": recommendations,
        "resources": [],
        "terraform_template": terraform_template,
        "estimatedCost": "Varies depending on usage",
        "warnings": ["This is a basic analysis without AI assistance. For more detailed recommendations, please provide a Google API key."]
    }

def generate_fallback_terraform_template(services, language, framework):
    """
    Generate a basic Terraform template based on detected services
    
    Args:
        services (list): Detected AWS services
        language (str): Programming language
        framework (dict): Framework information
        
    Returns:
        str: Basic Terraform template
    """
    template = """# Basic AWS Infrastructure Terraform Template
# Generated by Inframate (without AI assistance)

provider "aws" {
  region = var.region
}

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
"""
    
    # Add resources based on detected services
    resources_added = []
    
    if "S3" in services and framework.get("frontend"):
        # Add S3 static website hosting for frontend
        template += """
# S3 bucket for frontend hosting
resource "aws_s3_bucket" "frontend" {
  bucket = "${var.app_name}-${var.environment}-frontend"
  
  tags = {
    Name        = "${var.app_name}-frontend"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_website_configuration" "frontend_website" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

resource "aws_s3_bucket_ownership_controls" "frontend_ownership" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend_public_access" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_acl" "frontend_acl" {
  depends_on = [
    aws_s3_bucket_ownership_controls.frontend_ownership,
    aws_s3_bucket_public_access_block.frontend_public_access,
  ]

  bucket = aws_s3_bucket.frontend.id
  acl    = "public-read"
}

resource "aws_s3_bucket_policy" "frontend_policy" {
  bucket = aws_s3_bucket.frontend.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend.arn}/*"
      }
    ]
  })
}

output "frontend_website_endpoint" {
  value = aws_s3_bucket_website_configuration.frontend_website.website_endpoint
}
"""
        resources_added.append("S3")
    
    if "CloudFront" in services and "S3" in resources_added:
        # Add CloudFront distribution for S3
        template += """
# CloudFront distribution for the frontend
resource "aws_cloudfront_distribution" "frontend_distribution" {
  origin {
    domain_name = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id   = aws_s3_bucket.frontend.id
  }
  
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100"
  
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = aws_s3_bucket.frontend.id
    
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
  
  tags = {
    Name        = "${var.app_name}-distribution"
    Environment = var.environment
  }
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.frontend_distribution.domain_name
}
"""
        resources_added.append("CloudFront")
    
    if "Lambda" in services and (language == "Python" or language == "JavaScript/Node.js"):
        # Add Lambda function
        runtime = "python3.9" if language == "Python" else "nodejs18.x"
        handler = "index.handler" if language == "Python" else "index.handler"
        
        template += f"""
# Lambda function for backend
resource "aws_lambda_function" "backend" {{
  function_name    = "${{var.app_name}}-${{var.environment}}-backend"
  handler          = "{handler}"
  runtime          = "{runtime}"
  filename         = "lambda.zip"  # You'll need to create this deployment package
  source_code_hash = filebase64sha256("lambda.zip")
  
  role = aws_iam_role.lambda_role.arn
  
  environment {{
    variables = {{
      ENVIRONMENT = var.environment
    }}
  }}
  
  tags = {{
    Name        = "${{var.app_name}}-backend"
    Environment = var.environment
  }}
}}

# IAM role for Lambda
resource "aws_iam_role" "lambda_role" {{
  name = "${{var.app_name}}-${{var.environment}}-lambda-role"
  
  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {{
          Service = "lambda.amazonaws.com"
        }}
      }}
    ]
  }})
}}

# Basic execution policy for Lambda
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {{
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}}

output "lambda_function_name" {{
  value = aws_lambda_function.backend.function_name
}}

output "lambda_function_arn" {{
  value = aws_lambda_function.backend.arn
}}
"""
        resources_added.append("Lambda")
    
    if "API Gateway" in services and "Lambda" in resources_added:
        # Add API Gateway
        template += """
# API Gateway for the Lambda function
resource "aws_api_gateway_rest_api" "api" {
  name        = "${var.app_name}-${var.environment}-api"
  description = "API Gateway for ${var.app_name}"
}

resource "aws_api_gateway_resource" "resource" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.resource.id
  http_method   = "ANY"
  authorization_type = "NONE"
}

resource "aws_api_gateway_integration" "integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.resource.id
  http_method = aws_api_gateway_method.method.http_method
  
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.backend.invoke_arn
}

resource "aws_api_gateway_deployment" "deployment" {
  depends_on = [
    aws_api_gateway_integration.integration
  ]
  
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = var.environment
}

resource "aws_lambda_permission" "apigw_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backend.function_name
  principal     = "apigateway.amazonaws.com"
  
  source_arn = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

output "api_endpoint" {
  value = aws_api_gateway_deployment.deployment.invoke_url
}
"""
        resources_added.append("API Gateway")
    
    if "RDS" in services:
        # Add RDS database
        template += """
# RDS Database
resource "aws_db_instance" "database" {
  identifier             = "${var.app_name}-${var.environment}-db"
  allocated_storage      = 20
  storage_type           = "gp2"
  engine                 = "postgres"
  engine_version         = "13.7"
  instance_class         = "db.t3.micro"
  db_name                = "app"
  username               = "appuser"
  password               = "YourStrongPasswordHere123!"  # Change this and use a secure method to store passwords
  parameter_group_name   = "default.postgres13"
  skip_final_snapshot    = true
  backup_retention_period = 7
  
  tags = {
    Name        = "${var.app_name}-database"
    Environment = var.environment
  }
}

output "database_endpoint" {
  value = aws_db_instance.database.endpoint
}
"""
        resources_added.append("RDS")
    
    # If no resources were added, add a placeholder comment
    if not resources_added:
        template += """
# No specific resources were detected
# Add your resources here based on your application needs
"""
    
    return template 