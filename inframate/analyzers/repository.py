"""
Repository analyzer module
"""
import os
import json
from pathlib import Path
from git import Repo, InvalidGitRepositoryError
import glob
from typing import Dict, Any, List, Optional

from inframate.analyzers.framework import detect_framework
from inframate.analyzers.infrastructure import detect_infrastructure
from inframate.agents.ai_analyzer import analyze_with_ai

def analyze_repository(repo_path: str) -> Dict[str, Any]:
    """
    Analyze the structure of a repository to determine its
    language, framework, and infrastructure requirements
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary containing analysis results
    """
    repo_info = {
        "languages": detect_languages(repo_path),
        "frameworks": detect_frameworks(repo_path),
        "database": detect_database(repo_path),
        "file_structure": analyze_file_structure(repo_path),
        "has_docker": has_docker(repo_path),
        "has_kubernetes": has_kubernetes(repo_path),
        "has_terraform": has_terraform(repo_path),
        "dependencies": analyze_dependencies(repo_path)
    }
    
    # Try to extract README
    readme_path = find_file(repo_path, "README.md")
    if readme_path:
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                repo_info["readme"] = f.read()
        except Exception as e:
            print(f"Failed to read README: {e}")
    
    # Auto-detect language and framework if not specified in inframate.md
    inframate_md = Path(repo_path) / "inframate.md"
    if inframate_md.exists():
        try:
            with open(inframate_md, 'r', encoding='utf-8') as f:
                content = f.read()
                
            sections = content.split("##")
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                    
                lines = section.split('\n', 1)
                title = lines[0].strip().lower()
                
                if len(lines) > 1:
                    value = lines[1].strip()
                    
                    if title == 'language' and value.lower() == 'detected automatically':
                        # Use detected language
                        primary_language = get_primary_language(repo_info["languages"])
                        repo_info["language"] = primary_language
                    elif title == 'language':
                        repo_info["language"] = value
                        
                    if title == 'framework' and value.lower() == 'detected automatically':
                        # Use detected framework
                        primary_framework = get_primary_framework(repo_info["frameworks"])
                        repo_info["framework"] = primary_framework
                    elif title == 'framework':
                        repo_info["framework"] = value
                        
                    if title == 'database' and value.lower() == 'detected automatically':
                        repo_info["database_type"] = repo_info["database"]
                    elif title == 'database':
                        repo_info["database_type"] = value
                        
                    if title == "requirements":
                        repo_info["requirements"] = value
                        
                    if title == "description":
                        repo_info["description"] = value
        except Exception as e:
            print(f"Failed to parse inframate.md: {e}")
    
    return repo_info

def detect_languages(repo_path: str) -> Dict[str, float]:
    """
    Detect programming languages used in the repository
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary mapping language names to their usage percentage
    """
    # Count files by extension
    extension_counts = {}
    total_files = 0
    
    for root, _, files in os.walk(repo_path):
        # Skip hidden directories
        if os.path.basename(root).startswith('.'):
            continue
            
        for file in files:
            # Skip hidden files
            if file.startswith('.'):
                continue
                
            _, ext = os.path.splitext(file)
            if ext:
                ext = ext.lower()
                extension_counts[ext] = extension_counts.get(ext, 0) + 1
                total_files += 1
    
    # Map extensions to languages
    extension_to_language = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'JavaScript',
        '.tsx': 'TypeScript',
        '.java': 'Java',
        '.go': 'Go',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.cs': 'C#',
        '.c': 'C',
        '.cpp': 'C++',
        '.rs': 'Rust',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'SASS',
        '.sh': 'Shell',
        '.bash': 'Bash'
    }
    
    # Calculate language percentages
    languages = {}
    for ext, count in extension_counts.items():
        language = extension_to_language.get(ext)
        if language and total_files > 0:
            percentage = (count / total_files) * 100
            languages[language] = languages.get(language, 0) + percentage
    
    return languages

def detect_frameworks(repo_path: str) -> Dict[str, float]:
    """
    Detect frameworks used in the repository
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary mapping framework names to confidence scores
    """
    frameworks = {}
    
    # Check for package.json (Node.js)
    package_json_path = find_file(repo_path, "package.json")
    if package_json_path:
        try:
            with open(package_json_path, 'r') as f:
                data = json.load(f)
                dependencies = data.get('dependencies', {})
                dev_dependencies = data.get('devDependencies', {})
                all_deps = {**dependencies, **dev_dependencies}
                
                if 'react' in all_deps:
                    frameworks['React'] = 0.9
                if 'vue' in all_deps:
                    frameworks['Vue'] = 0.9
                if 'angular' in all_deps or '@angular/core' in all_deps:
                    frameworks['Angular'] = 0.9
                if 'next' in all_deps:
                    frameworks['Next.js'] = 0.9
                if 'nuxt' in all_deps:
                    frameworks['Nuxt.js'] = 0.9
                if 'express' in all_deps:
                    frameworks['Express'] = 0.9
                if 'nestjs' in all_deps or '@nestjs/core' in all_deps:
                    frameworks['NestJS'] = 0.9
                if 'koa' in all_deps:
                    frameworks['Koa'] = 0.9
                if 'meteor' in all_deps:
                    frameworks['Meteor'] = 0.8
        except Exception as e:
            print(f"Failed to parse package.json: {e}")
    
    # Check for requirements.txt (Python)
    requirements_path = find_file(repo_path, "requirements.txt")
    if requirements_path:
        try:
            with open(requirements_path, 'r') as f:
                content = f.read().lower()
                
                if 'django' in content:
                    frameworks['Django'] = 0.9
                if 'flask' in content:
                    frameworks['Flask'] = 0.9
                if 'fastapi' in content:
                    frameworks['FastAPI'] = 0.9
                if 'tornado' in content:
                    frameworks['Tornado'] = 0.8
                if 'pyramid' in content:
                    frameworks['Pyramid'] = 0.8
        except Exception as e:
            print(f"Failed to parse requirements.txt: {e}")
    
    # Check for Gemfile (Ruby)
    gemfile_path = find_file(repo_path, "Gemfile")
    if gemfile_path:
        try:
            with open(gemfile_path, 'r') as f:
                content = f.read().lower()
                
                if 'rails' in content:
                    frameworks['Ruby on Rails'] = 0.9
                if 'sinatra' in content:
                    frameworks['Sinatra'] = 0.8
        except Exception as e:
            print(f"Failed to parse Gemfile: {e}")
    
    # Check for pom.xml (Java)
    pom_path = find_file(repo_path, "pom.xml")
    if pom_path:
        try:
            with open(pom_path, 'r') as f:
                content = f.read().lower()
                
                if 'spring-boot' in content or 'springframework' in content:
                    frameworks['Spring Boot'] = 0.9
                if 'quarkus' in content:
                    frameworks['Quarkus'] = 0.9
                if 'micronaut' in content:
                    frameworks['Micronaut'] = 0.8
        except Exception as e:
            print(f"Failed to parse pom.xml: {e}")
    
    # Check for composer.json (PHP)
    composer_path = find_file(repo_path, "composer.json")
    if composer_path:
        try:
            with open(composer_path, 'r') as f:
                data = json.load(f)
                require = data.get('require', {})
                
                if 'laravel/framework' in require:
                    frameworks['Laravel'] = 0.9
                if 'symfony/symfony' in require:
                    frameworks['Symfony'] = 0.9
        except Exception as e:
            print(f"Failed to parse composer.json: {e}")
    
    return frameworks

def detect_database(repo_path: str) -> str:
    """
    Detect database used in the repository
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Database type as a string
    """
    # Look for database configuration files and dependencies
    
    # Check for package.json (Node.js)
    package_json_path = find_file(repo_path, "package.json")
    if package_json_path:
        try:
            with open(package_json_path, 'r') as f:
                data = json.load(f)
                dependencies = data.get('dependencies', {})
                
                if 'mongoose' in dependencies or 'mongodb' in dependencies:
                    return 'MongoDB'
                if 'pg' in dependencies or 'sequelize' in dependencies:
                    return 'PostgreSQL'
                if 'mysql' in dependencies or 'mysql2' in dependencies:
                    return 'MySQL'
                if 'redis' in dependencies:
                    return 'Redis'
                if 'dynamodb' in dependencies or 'aws-sdk' in dependencies:
                    return 'DynamoDB'
        except Exception as e:
            print(f"Failed to parse package.json: {e}")
    
    # Check for requirements.txt (Python)
    requirements_path = find_file(repo_path, "requirements.txt")
    if requirements_path:
        try:
            with open(requirements_path, 'r') as f:
                content = f.read().lower()
                
                if 'pymongo' in content:
                    return 'MongoDB'
                if 'psycopg2' in content or 'psycopg2-binary' in content:
                    return 'PostgreSQL'
                if 'mysql' in content:
                    return 'MySQL'
                if 'redis' in content:
                    return 'Redis'
                if 'pynamodb' in content or 'boto3' in content:
                    return 'DynamoDB'
        except Exception as e:
            print(f"Failed to parse requirements.txt: {e}")
    
    # Check for environment variables
    env_path = find_file(repo_path, ".env")
    if env_path:
        try:
            with open(env_path, 'r') as f:
                content = f.read().lower()
                
                if 'mongo' in content:
                    return 'MongoDB'
                if 'postgre' in content:
                    return 'PostgreSQL'
                if 'mysql' in content:
                    return 'MySQL'
                if 'redis' in content:
                    return 'Redis'
                if 'dynamodb' in content:
                    return 'DynamoDB'
        except Exception as e:
            print(f"Failed to parse .env: {e}")
    
    # Default to unknown
    return 'Unknown'

def analyze_file_structure(repo_path: str) -> Dict[str, Any]:
    """
    Analyze the file structure of the repository
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary containing file structure information
    """
    # Get top-level directories
    top_dirs = []
    dir_counts = {}
    file_counts = {}
    total_files = 0
    total_dirs = 0
    
    for item in os.listdir(repo_path):
        item_path = os.path.join(repo_path, item)
        
        # Skip hidden files
        if item.startswith('.'):
            continue
            
        if os.path.isdir(item_path):
            top_dirs.append(item)
            total_dirs += 1
    
    # Count files by type
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            # Skip hidden files
            if file.startswith('.'):
                continue
                
            _, ext = os.path.splitext(file)
            if ext:
                ext = ext.lower()
                file_counts[ext] = file_counts.get(ext, 0) + 1
                total_files += 1
    
    return {
        "top_dirs": top_dirs,
        "total_dirs": total_dirs,
        "total_files": total_files,
        "file_counts": file_counts
    }

def has_docker(repo_path: str) -> bool:
    """
    Check if the repository uses Docker
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        True if Docker is used, False otherwise
    """
    docker_files = ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml']
    for file in docker_files:
        if os.path.exists(os.path.join(repo_path, file)):
            return True
    
    return False

def has_kubernetes(repo_path: str) -> bool:
    """
    Check if the repository uses Kubernetes
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        True if Kubernetes is used, False otherwise
    """
    # Check for kubernetes directory or helm directory
    k8s_dirs = ['kubernetes', 'k8s', 'helm', 'manifests']
    for dir_name in k8s_dirs:
        if os.path.exists(os.path.join(repo_path, dir_name)):
            return True
    
    # Check for kubernetes YAML files
    yaml_files = glob.glob(os.path.join(repo_path, '**/*.yaml'), recursive=True)
    yaml_files.extend(glob.glob(os.path.join(repo_path, '**/*.yml'), recursive=True))
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r') as f:
                content = f.read()
                if 'apiVersion:' in content and 'kind:' in content:
                    return True
        except Exception:
            pass
    
    return False

def has_terraform(repo_path: str) -> bool:
    """
    Check if the repository uses Terraform
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        True if Terraform is used, False otherwise
    """
    # Check for .tf files
    tf_files = glob.glob(os.path.join(repo_path, '**/*.tf'), recursive=True)
    if tf_files:
        return True
    
    # Check for terraform directory
    if os.path.exists(os.path.join(repo_path, 'terraform')):
        return True
    
    return False

def analyze_dependencies(repo_path: str) -> Dict[str, Any]:
    """
    Analyze dependencies in the repository
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary containing dependency information
    """
    dependencies = {}
    
    # Check for package.json (Node.js)
    package_json_path = find_file(repo_path, "package.json")
    if package_json_path:
        try:
            with open(package_json_path, 'r') as f:
                data = json.load(f)
                dependencies['node'] = {
                    'dependencies': data.get('dependencies', {}),
                    'devDependencies': data.get('devDependencies', {})
                }
        except Exception as e:
            print(f"Failed to parse package.json: {e}")
    
    # Check for requirements.txt (Python)
    requirements_path = find_file(repo_path, "requirements.txt")
    if requirements_path:
        try:
            python_deps = []
            with open(requirements_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        python_deps.append(line)
            
            dependencies['python'] = {
                'requirements': python_deps
            }
        except Exception as e:
            print(f"Failed to parse requirements.txt: {e}")
    
    # Check for Gemfile (Ruby)
    gemfile_path = find_file(repo_path, "Gemfile")
    if gemfile_path:
        try:
            ruby_deps = []
            with open(gemfile_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('gem '):
                        ruby_deps.append(line)
            
            dependencies['ruby'] = {
                'gems': ruby_deps
            }
        except Exception as e:
            print(f"Failed to parse Gemfile: {e}")
    
    return dependencies

def find_file(repo_path: str, filename: str) -> Optional[str]:
    """
    Find a file in the repository by name
    
    Args:
        repo_path: Path to the repository
        filename: Filename to find
        
    Returns:
        Path to the file, or None if not found
    """
    for root, _, files in os.walk(repo_path):
        if filename in files:
            return os.path.join(root, filename)
    
    return None

def get_primary_language(languages: Dict[str, float]) -> str:
    """
    Get the primary language from a dictionary of languages and their percentages
    
    Args:
        languages: Dictionary mapping language names to their usage percentage
        
    Returns:
        Primary language name
    """
    if not languages:
        return "Unknown"
    
    primary_language = max(languages.items(), key=lambda x: x[1])[0]
    return primary_language

def get_primary_framework(frameworks: Dict[str, float]) -> str:
    """
    Get the primary framework from a dictionary of frameworks and their confidence scores
    
    Args:
        frameworks: Dictionary mapping framework names to their confidence scores
        
    Returns:
        Primary framework name
    """
    if not frameworks:
        return "None"
    
    primary_framework = max(frameworks.items(), key=lambda x: x[1])[0]
    return primary_framework

def analyze_repository_old(repo_path, verbose=False):
    """
    Analyzes a repository to understand its deployment requirements
    
    Args:
        repo_path (str): Path to the repository
        verbose (bool): Whether to show detailed output
        
    Returns:
        dict: Analysis results
    """
    if verbose:
        print("Starting repository analysis...")
    
    # Check if it's a git repository
    is_git_repo = False
    try:
        repo = Repo(repo_path)
        is_git_repo = True
    except InvalidGitRepositoryError:
        pass
    
    # Check if there's an Inframate config file
    inframate_path = os.path.join(repo_path, '.inframate.yaml')
    has_inframate_config = os.path.exists(inframate_path)
    
    config = {}
    if has_inframate_config:
        try:
            with open(inframate_path, 'r') as file:
                config = yaml.safe_load(file)
            if verbose:
                print("Found .inframate.yaml configuration")
        except Exception as e:
            print(f"Failed to parse .inframate.yaml: {str(e)}")
    
    # Read README.md if it exists
    readme_path = os.path.join(repo_path, 'README.md')
    readme = None
    if os.path.exists(readme_path):
        try:
            with open(readme_path, 'r') as file:
                readme = file.read()
            if verbose:
                print("Found README.md")
        except Exception as e:
            print(f"Failed to read README.md: {str(e)}")
    
    # Detect framework and infrastructure
    framework = detect_framework(repo_path, verbose)
    infrastructure = detect_infrastructure(repo_path, verbose)
    
    # Use AI to analyze the repository and generate recommendations
    ai_analysis = analyze_with_ai(repo_path, {
        "readme": readme,
        "framework": framework,
        "infrastructure": infrastructure,
        "config": config,
        "verbose": verbose
    })
    
    return {
        "repository_path": repo_path,
        "is_git_repo": is_git_repo,
        "has_inframate_config": has_inframate_config,
        "config": config,
        "framework": framework,
        "infrastructure": infrastructure,
        "detected_languages": ai_analysis.get("languages", []),
        "detected_services": ai_analysis.get("services", []),
        "recommendations": ai_analysis.get("recommendations", []),
        "suggested_resources": ai_analysis.get("resources", []),
        "estimated_cost": ai_analysis.get("estimatedCost", "Unknown"),
        "warnings": ai_analysis.get("warnings", [])
    } 