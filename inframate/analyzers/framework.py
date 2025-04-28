"""
Framework detection module for Inframate
"""
import os
import json
from pathlib import Path

def detect_framework(repo_path, verbose=False):
    """
    Detects frameworks used in the repository
    
    Args:
        repo_path (str): Path to the repository
        verbose (bool): Whether to show detailed output
        
    Returns:
        dict: Detected frameworks
    """
    if verbose:
        print("Detecting frameworks...")
    
    result = {
        "language": None,
        "frontend": None,
        "backend": None,
        "database": None,
        "other": []
    }
    
    # Check for package.json (Node.js)
    package_json_path = os.path.join(repo_path, 'package.json')
    if os.path.exists(package_json_path):
        try:
            with open(package_json_path, 'r') as file:
                package_json = json.load(file)
            
            result["language"] = "JavaScript/Node.js"
            
            # Combine dependencies and devDependencies
            deps = {}
            if "dependencies" in package_json:
                deps.update(package_json["dependencies"])
            if "devDependencies" in package_json:
                deps.update(package_json["devDependencies"])
            
            # Frontend frameworks
            if "react" in deps:
                result["frontend"] = "React"
            elif "vue" in deps:
                result["frontend"] = "Vue.js"
            elif "angular" in deps:
                result["frontend"] = "Angular"
            elif "svelte" in deps:
                result["frontend"] = "Svelte"
            
            # Backend frameworks
            if "express" in deps:
                result["backend"] = "Express"
            elif "fastify" in deps:
                result["backend"] = "Fastify"
            elif "koa" in deps:
                result["backend"] = "Koa"
            elif "nest" in deps or "@nestjs/core" in deps:
                result["backend"] = "NestJS"
            
            # Serverless
            if "serverless" in deps or os.path.exists(os.path.join(repo_path, 'serverless.yml')):
                result["other"].append("Serverless Framework")
            
            # Database ORMs
            if "mongoose" in deps:
                result["database"] = "MongoDB (Mongoose)"
            elif "sequelize" in deps:
                result["database"] = "SQL (Sequelize)"
            elif "prisma" in deps:
                result["database"] = "Prisma"
            elif "typeorm" in deps:
                result["database"] = "TypeORM"
            
            if verbose:
                print(f"Detected Node.js project with {result['frontend'] or 'no'} frontend and {result['backend'] or 'no'} backend")
        
        except Exception as e:
            print(f"Error parsing package.json: {str(e)}")
    
    # Check for requirements.txt or setup.py (Python)
    requirements_path = os.path.join(repo_path, 'requirements.txt')
    setup_py_path = os.path.join(repo_path, 'setup.py')
    
    if os.path.exists(requirements_path) or os.path.exists(setup_py_path):
        result["language"] = "Python"
        
        requirements = ""
        if os.path.exists(requirements_path):
            try:
                with open(requirements_path, 'r') as file:
                    requirements = file.read()
            except Exception as e:
                print(f"Error reading requirements.txt: {str(e)}")
        
        # Check for Python frameworks
        if "django" in requirements.lower():
            result["backend"] = "Django"
        elif "flask" in requirements.lower():
            result["backend"] = "Flask"
        elif "fastapi" in requirements.lower():
            result["backend"] = "FastAPI"
        
        if "sqlalchemy" in requirements.lower():
            result["database"] = "SQLAlchemy"
        
        if verbose:
            print(f"Detected Python project with {result['backend'] or 'no'} framework")
    
    # Check for Dockerfile
    if os.path.exists(os.path.join(repo_path, 'Dockerfile')) or os.path.exists(os.path.join(repo_path, 'docker-compose.yml')):
        result["other"].append("Docker")
    
    # Check for .tf files (Terraform)
    main_tf_path = os.path.join(repo_path, 'main.tf')
    has_terraform = os.path.exists(main_tf_path) or len(find_files_with_extension(repo_path, '.tf')) > 0
    
    if has_terraform:
        result["other"].append("Terraform")
    
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