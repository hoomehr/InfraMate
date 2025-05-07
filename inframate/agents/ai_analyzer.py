"""
AI-powered repository analyzer using Google Gemini
"""
import os
import json
import yaml
import google.generativeai as genai
from dotenv import load_dotenv
from inframate.utils.rag import RAGManager
from inframate.utils.cost_estimator import estimate_costs
from inframate.utils.template_manager import TemplateManager
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

# Load environment variables
load_dotenv()

# Get API key from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Check if debug mode is enabled
DEBUG_MODE = os.getenv("INFRAMATE_DEBUG", "0") == "1"

# Initialize RAG manager and template manager
rag_manager = RAGManager()
template_manager = TemplateManager()

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
4. A monthly cost estimation for the infrastructure resources

Format your response with clear sections:
RECOMMENDED_SERVICES: (comma-separated list of AWS services)
RECOMMENDATIONS: (bullet points for infrastructure recommendations)
COST_ESTIMATION: (Monthly cost estimation with breakdown by service type)
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
        
        # Debug info
        if DEBUG_MODE:
            print("\n=== SENDING PROMPT TO GEMINI API ===")
            print(f"API URL: {url}")
            print(f"Prompt length: {len(prompt)} characters")
            print("First 500 chars of prompt:")
            print(prompt[:500])
            print("...")
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            print(f"Warning: Gemini API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return fallback_analyze(repo_info)
        
        response_data = response.json()
        
        # Debug info for response
        if DEBUG_MODE:
            print("\n=== RECEIVED RESPONSE FROM GEMINI API ===")
            print(f"Status code: {response.status_code}")
            print(f"Response size: {len(response.text)} characters")
            print("Full response JSON:")
            print(json.dumps(response_data, indent=2))
        
        # Extract the text from the response
        ai_response = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        # Debug info for parsed response
        if DEBUG_MODE:
            print("\n=== PARSED AI RESPONSE ===")
            print(f"Response text length: {len(ai_response)} characters")
            print("First 1000 chars of response:")
            print(ai_response[:1000])
            print("...")
        
        # Parse the response to extract the services, recommendations, and Terraform template
        services = []
        recommendations = []
        terraform_template = ""
        cost_estimation = ""
        
        if "RECOMMENDED_SERVICES:" in ai_response:
            services_section = ai_response.split("RECOMMENDED_SERVICES:")[1].split("RECOMMENDATIONS:")[0].strip()
            services = [service.strip() for service in services_section.split(",")]
            
            # Debug info for services
            if DEBUG_MODE:
                print("\n=== EXTRACTED SERVICES ===")
                print(f"Number of services: {len(services)}")
                print(services)
        
        if "RECOMMENDATIONS:" in ai_response:
            recommendations_section = ai_response.split("RECOMMENDATIONS:")[1].split("COST_ESTIMATION:")[0].strip() if "COST_ESTIMATION:" in ai_response else ai_response.split("RECOMMENDATIONS:")[1].split("TERRAFORM_TEMPLATE:")[0].strip()
            recommendations = [rec.strip().lstrip("- ") for rec in recommendations_section.split("\n") if rec.strip()]
            
            # Debug info for recommendations
            if DEBUG_MODE:
                print("\n=== EXTRACTED RECOMMENDATIONS ===")
                print(f"Number of recommendations: {len(recommendations)}")
                for i, rec in enumerate(recommendations):
                    print(f"{i+1}. {rec}")
        
        if "COST_ESTIMATION:" in ai_response:
            cost_section = ai_response.split("COST_ESTIMATION:")[1].split("TERRAFORM_TEMPLATE:")[0].strip()
            cost_estimation = cost_section
            
            # Debug info for cost estimation
            if DEBUG_MODE:
                print("\n=== EXTRACTED COST ESTIMATION ===")
                print(cost_estimation)
        
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
            
            # Debug info for terraform template
            if DEBUG_MODE:
                print("\n=== EXTRACTED TERRAFORM TEMPLATE ===")
                print(f"Template length: {len(terraform_template)} characters")
                print("First 500 chars of template:")
                print(terraform_template[:500])
                print("...")
        
        return {
            "services": services,
            "recommendations": recommendations,
            "terraform_template": terraform_template,
            "cost_estimation": cost_estimation,
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
    elif 'mysql' in database or 'mariadb' in database:
        services.append("RDS")
        recommendations.append("Use Amazon RDS for MySQL/MariaDB")
    elif 'postgres' in database or 'postgresql' in database:
        services.append("RDS")
        recommendations.append("Use Amazon RDS for PostgreSQL")
    elif 'redis' in database:
        services.append("ElastiCache")
        recommendations.append("Use Amazon ElastiCache for Redis")
    
    # Default services if none were identified
    if not services:
        services = ["EC2", "VPC", "S3", "CloudWatch"]
        recommendations.append("Use basic EC2 setup with VPC and S3 storage")
    
    # Default recommendations if none were identified
    if not recommendations:
        recommendations = [
            "Use Infrastructure as Code (IaC) with Terraform",
            "Implement monitoring and logging with CloudWatch",
            "Set up auto-scaling for handling traffic spikes",
            "Configure proper security groups and IAM roles"
        ]
    
    # Use the cost estimator to generate cost estimation
    cost_result = estimate_costs(services)
    cost_estimation = cost_result["cost_estimation"]
    
    # Use template manager to generate Terraform template
    terraform_template = template_manager.get_template_for_services(services)
    
    return {
        "services": services,
        "recommendations": recommendations,
        "terraform_template": terraform_template,
        "cost_estimation": cost_estimation
    } 