"""
Infrastructure detection module for Inframate
"""
import os
import yaml
from pathlib import Path
import re

def detect_infrastructure(repo_path, verbose=False):
    """
    Detects infrastructure configuration in the repository
    
    Args:
        repo_path (str): Path to the repository
        verbose (bool): Whether to show detailed output
        
    Returns:
        dict: Detected infrastructure
    """
    if verbose:
        print("Detecting infrastructure configuration...")
    
    result = {
        "type": None,
        "configuration": None,
        "aws": {
            "detected": False,
            "services": []
        },
        "azure": {
            "detected": False,
            "services": []
        },
        "gcp": {
            "detected": False,
            "services": []
        },
        "cloudformation": False,
        "terraform": False,
        "kubernetes": False,
        "docker": False
    }
    
    # Check for CloudFormation templates
    cf_template_paths = [
        os.path.join(repo_path, 'template.yaml'),
        os.path.join(repo_path, 'template.yml'),
        os.path.join(repo_path, 'cloudformation.yaml'),
        os.path.join(repo_path, 'cloudformation.yml')
    ]
    
    for template_path in cf_template_paths:
        if os.path.exists(template_path):
            result["type"] = "CloudFormation"
            result["cloudformation"] = True
            result["aws"]["detected"] = True
            
            try:
                with open(template_path, 'r') as file:
                    template = yaml.safe_load(file)
                
                result["configuration"] = template
                
                # Detect AWS services from CloudFormation resources
                if template and "Resources" in template:
                    for resource_key, resource in template["Resources"].items():
                        if "Type" in resource:
                            service_match = re.match(r'^AWS::([^:]+)', resource["Type"])
                            if (service_match and service_match.group(1) and 
                                service_match.group(1) not in result["aws"]["services"]):
                                result["aws"]["services"].append(service_match.group(1))
                
                if verbose:
                    services_str = ", ".join(result["aws"]["services"]) if result["aws"]["services"] else "none"
                    print(f"Detected CloudFormation template with AWS services: {services_str}")
                break
            
            except Exception as e:
                print(f"Error parsing CloudFormation template ({template_path}): {str(e)}")
    
    # Check for Terraform files
    tf_files = find_files_with_extension(repo_path, '.tf')
    if tf_files:
        result["type"] = "Terraform"
        result["terraform"] = True
        
        # Simple check for cloud providers in Terraform files
        for tf_file in tf_files:
            try:
                with open(tf_file, 'r') as file:
                    content = file.read()
                
                if 'provider "aws"' in content:
                    result["aws"]["detected"] = True
                if 'provider "azurerm"' in content:
                    result["azure"]["detected"] = True
                if 'provider "google"' in content:
                    result["gcp"]["detected"] = True
            
            except Exception as e:
                print(f"Error reading Terraform file ({tf_file}): {str(e)}")
        
        if verbose:
            providers = []
            if result["aws"]["detected"]:
                providers.append("AWS")
            if result["azure"]["detected"]:
                providers.append("Azure")
            if result["gcp"]["detected"]:
                providers.append("GCP")
            
            providers_str = ", ".join(providers) if providers else "unknown"
            print(f"Detected Terraform configuration with providers: {providers_str}")
    
    # Check for Docker configuration
    dockerfile_path = os.path.join(repo_path, 'Dockerfile')
    docker_compose_path = os.path.join(repo_path, 'docker-compose.yml')
    
    if os.path.exists(dockerfile_path) or os.path.exists(docker_compose_path):
        result["docker"] = True
        if verbose:
            print("Detected Docker configuration")
    
    # Check for Kubernetes manifests
    k8s_files = []
    yaml_files = find_files_with_extension(repo_path, '.yaml')
    yaml_files.extend(find_files_with_extension(repo_path, '.yml'))
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r') as file:
                content = file.read()
                if ('apiVersion:' in content and 
                    ('kind: Deployment' in content or 
                     'kind: Service' in content or 
                     'kind: Pod' in content)):
                    k8s_files.append(yaml_file)
        except:
            pass
    
    if k8s_files:
        result["kubernetes"] = True
        if verbose:
            print("Detected Kubernetes manifests")
    
    # Check for AWS configuration
    serverless_yml = os.path.join(repo_path, 'serverless.yml')
    serverless_yaml = os.path.join(repo_path, 'serverless.yaml')
    
    if os.path.exists(serverless_yml) or os.path.exists(serverless_yaml):
        result["aws"]["detected"] = True
        if "Lambda" not in result["aws"]["services"]:
            result["aws"]["services"].append("Lambda")
        if verbose:
            print("Detected Serverless Framework (AWS Lambda)")
    
    amplify_yml = os.path.join(repo_path, 'amplify.yml')
    amplify_dir = os.path.join(repo_path, 'amplify')
    
    if os.path.exists(amplify_yml) or os.path.exists(amplify_dir):
        result["aws"]["detected"] = True
        if "Amplify" not in result["aws"]["services"]:
            result["aws"]["services"].append("Amplify")
        if verbose:
            print("Detected AWS Amplify")
    
    # Check for .aws directory or credentials
    aws_dir = os.path.join(repo_path, '.aws')
    aws_config = os.path.join(repo_path, 'aws-config.json')
    
    if os.path.exists(aws_dir) or os.path.exists(aws_config):
        result["aws"]["detected"] = True
        if verbose:
            print("Detected AWS configuration files")
    
    return result

def find_files_with_extension(directory, extension, files=None):
    """
    Find files with a specific extension in a directory
    
    Args:
        directory (str): Directory to search
        extension (str): File extension to look for
        files (list): Accumulator for recursive calls
        
    Returns:
        list: List of matching files
    """
    if files is None:
        files = []
    
    if not os.path.exists(directory):
        return files
    
    for entry in os.scandir(directory):
        if entry.is_dir() and not entry.name.startswith('.') and entry.name != 'node_modules':
            # Skip node_modules and hidden directories
            find_files_with_extension(entry.path, extension, files)
        elif entry.is_file() and entry.name.endswith(extension):
            files.append(entry.path)
    
    return files 