"""
AWS deployment provider
"""
import os
import boto3
import yaml
import json
import tempfile
import shutil
from pathlib import Path

def deploy_to_aws(repo_path, analysis, profile=None, region=None, verbose=False):
    """
    Deploy a repository to AWS
    
    Args:
        repo_path (str): Path to the repository
        analysis (dict): Analysis results
        profile (str): AWS profile to use
        region (str): AWS region to deploy to
        verbose (bool): Whether to show detailed output
        
    Returns:
        dict: Deployment results
    """
    if verbose:
        print("Starting AWS deployment...")
    
    # Configure AWS session
    session = configure_aws_session(profile, region)
    
    # Get region from session
    region = session.region_name or "us-east-1"
    
    # Get deployment configuration
    config = get_deployment_config(repo_path, analysis, region)
    
    if verbose:
        print(f"Deploying to AWS region: {region}")
        print(f"Using deployment configuration: {json.dumps(config, indent=2)}")
    
    # Check if we're using CloudFormation or direct resource creation
    if analysis["infrastructure"]["cloudformation"]:
        deployment_results = deploy_cloudformation(session, repo_path, config, verbose)
    elif "Terraform" in analysis["infrastructure"]["type"]:
        deployment_results = deploy_terraform(session, repo_path, config, verbose)
    else:
        deployment_results = deploy_resources(session, repo_path, config, verbose)
    
    return deployment_results

def configure_aws_session(profile=None, region=None):
    """
    Configure AWS session with the given profile and region
    
    Args:
        profile (str): AWS profile to use
        region (str): AWS region to deploy to
        
    Returns:
        boto3.Session: Configured AWS session
    """
    kwargs = {}
    
    if profile:
        kwargs["profile_name"] = profile
    
    if region:
        kwargs["region_name"] = region
    
    return boto3.Session(**kwargs)

def get_deployment_config(repo_path, analysis, region):
    """
    Get deployment configuration from Inframate config or analysis
    
    Args:
        repo_path (str): Path to the repository
        analysis (dict): Analysis results
        region (str): AWS region
        
    Returns:
        dict: Deployment configuration
    """
    # Default configuration
    config = {
        "region": region,
        "resources": []
    }
    
    # Check if there's an Inframate config file
    inframate_path = os.path.join(repo_path, '.inframate.yaml')
    if os.path.exists(inframate_path):
        try:
            with open(inframate_path, 'r') as file:
                user_config = yaml.safe_load(file)
            
            if user_config.get("region"):
                config["region"] = user_config["region"]
            
            if user_config.get("resources"):
                config["resources"] = user_config["resources"]
        except Exception as e:
            print(f"Error loading Inframate config: {str(e)}")
    
    # If no resources specified, use suggested resources from analysis
    if not config["resources"] and analysis.get("suggested_resources"):
        config["resources"] = analysis["suggested_resources"]
    
    # If still no resources, generate from detected services
    if not config["resources"] and analysis.get("detected_services"):
        config["resources"] = generate_resources_from_services(analysis["detected_services"])
    
    return config

def generate_resources_from_services(services):
    """
    Generate resource configurations from detected services
    
    Args:
        services (list): List of detected AWS services
        
    Returns:
        list: Resource configurations
    """
    resources = []
    
    if "Lambda" in services:
        resources.append({
            "type": "lambda",
            "name": "app-function",
            "runtime": "python3.9",
            "handler": "index.handler",
            "memory": 128,
            "timeout": 30
        })
    
    if "API Gateway" in services:
        resources.append({
            "type": "apigateway",
            "name": "app-api",
            "path": "/api",
            "method": "ANY"
        })
    
    if "S3" in services:
        resources.append({
            "type": "s3",
            "name": "app-bucket",
            "public": True
        })
    
    if "DynamoDB" in services:
        resources.append({
            "type": "dynamodb",
            "name": "app-table",
            "hashKey": "id",
            "readCapacity": 5,
            "writeCapacity": 5
        })
    
    if "RDS" in services:
        resources.append({
            "type": "rds",
            "name": "app-database",
            "engine": "postgres",
            "size": "db.t3.micro"
        })
    
    return resources

def deploy_cloudformation(session, repo_path, config, verbose=False):
    """
    Deploy using CloudFormation
    
    Args:
        session (boto3.Session): AWS session
        repo_path (str): Path to the repository
        config (dict): Deployment configuration
        verbose (bool): Whether to show detailed output
        
    Returns:
        dict: Deployment results
    """
    if verbose:
        print("Deploying using CloudFormation...")
    
    # Placeholder for actual CloudFormation deployment
    # In a real implementation, this would:
    # 1. Read the CloudFormation template
    # 2. Update it with the configuration
    # 3. Deploy the stack
    
    return {
        "message": "CloudFormation deployment not implemented in this version",
        "stack_name": "inframate-app-stack",
        "region": config["region"],
        "status": "DEMO_MODE"
    }

def deploy_terraform(session, repo_path, config, verbose=False):
    """
    Deploy using Terraform
    
    Args:
        session (boto3.Session): AWS session
        repo_path (str): Path to the repository
        config (dict): Deployment configuration
        verbose (bool): Whether to show detailed output
        
    Returns:
        dict: Deployment results
    """
    if verbose:
        print("Deploying using Terraform...")
    
    # Placeholder for actual Terraform deployment
    # In a real implementation, this would:
    # 1. Update the Terraform variables
    # 2. Run terraform init, plan, and apply
    
    return {
        "message": "Terraform deployment not implemented in this version",
        "state": "inframate-terraform-state",
        "region": config["region"],
        "status": "DEMO_MODE"
    }

def deploy_resources(session, repo_path, config, verbose=False):
    """
    Deploy resources directly using boto3
    
    Args:
        session (boto3.Session): AWS session
        repo_path (str): Path to the repository
        config (dict): Deployment configuration
        verbose (bool): Whether to show detailed output
        
    Returns:
        dict: Deployment results
    """
    if verbose:
        print("Deploying resources directly...")
    
    # Placeholder for actual resource deployment
    # In a real implementation, this would:
    # 1. Create each resource in the configuration
    # 2. Wait for the resources to be created
    # 3. Return the created resources
    
    return {
        "message": "Direct resource deployment not implemented in this version",
        "resources": config["resources"],
        "region": config["region"],
        "status": "DEMO_MODE"
    } 