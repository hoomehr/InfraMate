#!/usr/bin/env python3
"""
Inframate Flow - Read inframate.md, generate recommendations, and create TF folder with files
"""
import os
import sys
import json
import yaml
import shutil
import requests
from pathlib import Path
from typing import Dict, Any

# Import Inframate components
try:
    from inframate.analyzers.repository import analyze_repository
    from inframate.agents.ai_analyzer import analyze_with_ai, fallback_analyze, generate_terraform_template
    from inframate.utils.rag import RAGManager
except ImportError:
    print("Error: Inframate modules not found. Please make sure Inframate is installed correctly.")
    sys.exit(1)

# Gemini API key and endpoint
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-exp-03-25:generateContent"

def read_inframate_file(repo_path: str) -> Dict[str, Any]:
    """Read and parse the inframate.md file"""
    inframate_path = Path(repo_path) / "inframate.md"
    if not inframate_path.exists():
        raise FileNotFoundError("inframate.md file not found in repository")
    
    with open(inframate_path, "r") as f:
        content = f.read()
    
    # Basic parsing of markdown content
    # This is a simple implementation - you might want to enhance it
    sections = content.split("##")
    info = {}
    for section in sections[1:]:  # Skip the first empty section
        lines = section.strip().split("\n")
        title = lines[0].strip()
        content = "\n".join(lines[1:]).strip()
        info[title.lower()] = content
    
    return info

def analyze_repository(repo_path):
    """Analyze repository structure and requirements"""
    # Read inframate.md
    requirements = read_inframate_file(repo_path)
    
    # Get Gemini API key from environment
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in environment")
    
    # Call Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-exp-03-25:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    prompt = f"""
    Analyze the following application requirements and generate infrastructure recommendations:
    
    {requirements}
    
    Please provide:
    1. Recommended AWS services
    2. Infrastructure architecture
    3. Terraform configuration
    """
    
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise Exception(f"Gemini API error: {response.text}")
    
    return response.json()

def analyze_with_gemini(md_data):
    """Analyze repository data using Gemini API"""
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not set. Using fallback analysis.")
        return fallback_analyze(md_data)
    
    print("Using Gemini API to generate recommendations...")
    
    prompt = f"""
I have a {md_data['language']} application using {md_data['framework']} framework with {md_data['database']} database.
Here's the full description of my application and infrastructure requirements:

{md_data.get('full_content', '')}

Based on this information, please provide:
1. A list of recommended AWS services for deployment
2. Infrastructure recommendations for this application
3. A Terraform template for deploying this application to AWS

Format your response with clear sections for:
- RECOMMENDED_SERVICES: (comma-separated list)
- RECOMMENDATIONS: (bullet points)
- TERRAFORM_TEMPLATE: (complete, production-ready Terraform code)
"""
    
    try:
        # Prepare Gemini API request
        request_data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        # Add API key to URL
        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        
        # Make API request
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=request_data
        )
        
        # Check response status
        if response.status_code != 200:
            print(f"Error calling Gemini API: {response.status_code} - {response.text}")
            return fallback_analyze(md_data)
        
        # Parse response
        response_data = response.json()
        ai_response = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        # Extract services, recommendations, and Terraform template
        services = []
        recommendations = []
        terraform_template = ""
        
        if "RECOMMENDED_SERVICES:" in ai_response:
            services_text = ai_response.split("RECOMMENDED_SERVICES:")[1].split("\n")[0].strip()
            services = [service.strip() for service in services_text.split(",")]
        
        if "RECOMMENDATIONS:" in ai_response:
            recommendations_section = ai_response.split("RECOMMENDATIONS:")[1].split("TERRAFORM_TEMPLATE:")[0].strip()
            recommendations = [rec.strip().lstrip("- ") for rec in recommendations_section.split("\n") if rec.strip()]
        
        if "TERRAFORM_TEMPLATE:" in ai_response:
            template_section = ai_response.split("TERRAFORM_TEMPLATE:")[1].strip()
            # Find the Terraform code block which is often enclosed in ``` markers
            if "```terraform" in template_section and "```" in template_section:
                start = template_section.find("```terraform") + len("```terraform")
                end = template_section.find("```", start)
                terraform_template = template_section[start:end].strip()
            elif "```" in template_section:
                # Try to find a generic code block
                parts = template_section.split("```")
                if len(parts) > 1:
                    terraform_template = parts[1].strip()
            else:
                # Just use everything
                terraform_template = template_section
        
        return {
            "services": services,
            "recommendations": recommendations,
            "terraform_template": terraform_template
        }
        
    except Exception as e:
        print(f"Error using Gemini API: {str(e)}")
        return fallback_analyze(md_data)

def fallback_analyze(md_data):
    """Provide basic analysis when AI is not available"""
    print("Using fallback analysis without AI...")
    
    services = []
    recommendations = []
    
    # Detect services based on framework and language
    if "Node.js" in md_data["language"]:
        services.extend(["Lambda", "API Gateway"])
        
    if "Express" in md_data["framework"]:
        services.extend(["Lambda", "API Gateway"])
    
    if "MongoDB" in md_data["database"]:
        recommendations.append("Use MongoDB Atlas or DocumentDB for MongoDB database")
    
    # Check infrastructure requirements
    for req in md_data.get("requirements", []):
        if "high" in req.lower() and "available" in req.lower():
            recommendations.append("Deploy across multiple availability zones for high availability")
        
        if "auto" in req.lower() and "scale" in req.lower():
            services.append("Auto Scaling")
            recommendations.append("Configure auto-scaling for your application")
        
        if "https" in req.lower():
            services.append("CloudFront")
            recommendations.append("Use CloudFront with ACM for HTTPS support")
    
    # Deduplicate services
    services = list(set(services))
    
    return {
        "languages": [md_data["language"]],
        "services": services,
        "recommendations": recommendations,
        "terraform_template": generate_terraform_template(md_data, services)
    }

def generate_terraform_files(repo_path, analysis, md_data):
    """Create Terraform files in the root directory"""
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

def generate_terraform_template(md_data, services):
    """Generate Terraform template based on detected services"""
    # Detect the proper template to use
    if "Node.js" in md_data["language"] and "Express" in md_data["framework"]:
        return generate_nodejs_terraform(md_data)
    elif "Python" in md_data["language"]:
        return generate_python_terraform(md_data)
    else:
        return generate_generic_terraform(md_data)

def generate_nodejs_terraform(md_data):
    """Generate Terraform for Node.js/Express applications"""
    return """# Terraform configuration for Node.js/Express API with MongoDB
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

  tags = {
    Name        = "${var.app_name}-api"
    Environment = var.environment
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

# Attach basic Lambda execution role
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
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

# Integration with Lambda
resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy.http_method
  
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

# Handle root path
resource "aws_api_gateway_method" "root" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_rest_api.api.root_resource_id
  http_method   = "ANY"
  authorization_type = "NONE"
}

resource "aws_api_gateway_integration" "root" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_rest_api.api.root_resource_id
  http_method = aws_api_gateway_method.root.http_method
  
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

# Deploy the API
resource "aws_api_gateway_deployment" "api" {
  depends_on = [
    aws_api_gateway_integration.lambda,
    aws_api_gateway_integration.root
  ]
  
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = var.environment
}

# Permission for API Gateway to invoke Lambda
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  
  source_arn = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.api.function_name}"
  retention_in_days = 30
}

# Auto-scaling configuration for Lambda
resource "aws_appautoscaling_target" "lambda_target" {
  max_capacity       = 10
  min_capacity       = 1
  resource_id        = "function:${aws_lambda_function.api.function_name}:${aws_lambda_function.api.version}"
  scalable_dimension = "lambda:function:ProvisionedConcurrency"
  service_namespace  = "lambda"
}

resource "aws_appautoscaling_policy" "lambda_policy" {
  name               = "${var.app_name}-${var.environment}-autoscaling-policy"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.lambda_target.resource_id
  scalable_dimension = aws_appautoscaling_target.lambda_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.lambda_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "LambdaProvisionedConcurrencyUtilization"
    }
    target_value = 0.75
  }
}
"""

def generate_python_terraform(md_data):
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

  tags = {
    Name        = "${var.app_name}-api"
    Environment = var.environment
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

# Attach basic Lambda execution role
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
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

# Integration with Lambda
resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.proxy.http_method
  
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api.invoke_arn
}

# Deploy the API
resource "aws_api_gateway_deployment" "api" {
  depends_on = [
    aws_api_gateway_integration.lambda
  ]
  
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = var.environment
}

# Permission for API Gateway to invoke Lambda
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  
  source_arn = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}
"""

def generate_generic_terraform(md_data):
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
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS access"
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
  
  tags = {
    Name        = "${var.app_name}-sg"
    Environment = var.environment
  }
}
"""

def call_gemini_api(prompt, api_key=None):
    """Call Gemini API with the given prompt"""
    if not api_key:
        # Get Gemini API key from environment
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")
    
    # Call Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-exp-03-25:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise Exception(f"Gemini API error: {response.text}")
    
    return response.json()

def main():
    """Main entry point for Inframate"""
    if len(sys.argv) != 2:
        print("Usage: python inframate_flow.py <repository_path>")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    
    try:
        # Read repository information
        repo_info = read_inframate_file(repo_path)
        
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
        
        print("\n✅ Inframate infrastructure generation complete!")
        print(f"📁 Terraform files generated in: {terraform_dir}")
        
        # Display next steps as optional
        print("\n🔷 Next Steps (Optional):")
        print("  1. Review the generated Terraform files")
        print("  2. Initialize Terraform:         terraform -chdir=%s init" % terraform_dir)
        print("  3. Plan your infrastructure:     terraform -chdir=%s plan -out=tfplan" % terraform_dir)
        print("  4. Apply the infrastructure:     terraform -chdir=%s apply tfplan" % terraform_dir)
        print("  5. Deploy your application:      ./scripts/deploy.sh %s\n" % terraform_dir)
        
        # Create a helpful next-steps file in the terraform directory
        next_steps_file = os.path.join(terraform_dir, "NEXT_STEPS.md")
        with open(next_steps_file, 'w') as f:
            f.write("# Next Steps\n\n")
            f.write("Inframate has generated your infrastructure code. Follow these steps to deploy:\n\n")
            f.write("## 1. Review the Generated Files\n")
            f.write("- `main.tf`: Contains the main infrastructure resources\n")
            f.write("- `variables.tf`: Defines input variables\n")
            f.write("- `outputs.tf`: Defines outputs from the deployment\n")
            f.write("- `terraform.tfvars`: Contains default values for variables\n")
            f.write("- `README.md`: Documentation for the infrastructure\n\n")
            
            f.write("## 2. Initialize Terraform\n")
            f.write("```bash\n")
            f.write(f"cd {terraform_dir}\n")
            f.write("terraform init\n")
            f.write("```\n\n")
            
            f.write("## 3. Plan Your Infrastructure\n")
            f.write("```bash\n")
            f.write("terraform plan -out=tfplan\n")
            f.write("```\n\n")
            
            f.write("## 4. Apply the Infrastructure\n")
            f.write("```bash\n")
            f.write("terraform apply tfplan\n")
            f.write("```\n\n")
            
            f.write("## 5. Deploy Your Application\n")
            f.write("Depending on your application, you may need to deploy your code to the infrastructure.\n")
            f.write("Refer to the README.md for specific deployment instructions.\n")
        
        print(f"📝 A detailed guide has been saved to: {next_steps_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 