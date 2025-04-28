"""
Repository analyzer module
"""
import os
import json
from pathlib import Path
from git import Repo, InvalidGitRepositoryError

from inframate.analyzers.framework import detect_framework
from inframate.analyzers.infrastructure import detect_infrastructure
from inframate.agents.ai_analyzer import analyze_with_ai

def analyze_repository(repo_path):
    """Analyze a repository for infrastructure requirements"""
    try:
        # Initialize repository object
        repo = Repo(repo_path)
        
        # Read inframate.md
        md_path = Path(repo_path) / "inframate.md"
        if not md_path.exists():
            raise FileNotFoundError("inframate.md not found in repository")
        
        with open(md_path, 'r') as f:
            requirements = f.read()
        
        # Get repository information
        repo_info = {
            "name": os.path.basename(repo_path),
            "branch": repo.active_branch.name,
            "requirements": requirements,
            "files": [f for f in repo.git.ls_files().split('\n')],
            "languages": detect_languages(repo_path)
        }
        
        return repo_info
        
    except InvalidGitRepositoryError:
        raise ValueError(f"{repo_path} is not a valid Git repository")
    except Exception as e:
        raise Exception(f"Error analyzing repository: {str(e)}")

def detect_languages(repo_path):
    """Detect programming languages used in the repository"""
    # Common file extensions and their languages
    language_extensions = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.java': 'Java',
        '.go': 'Go',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.rs': 'Rust',
        '.cpp': 'C++',
        '.c': 'C',
        '.cs': 'C#',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.dart': 'Dart',
        '.sh': 'Shell',
        '.pl': 'Perl',
        '.lua': 'Lua',
        '.r': 'R',
        '.m': 'MATLAB',
        '.sql': 'SQL',
        '.html': 'HTML',
        '.css': 'CSS',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.xml': 'XML',
        '.md': 'Markdown'
    }
    
    detected_languages = set()
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in language_extensions:
                detected_languages.add(language_extensions[ext])
    
    return list(detected_languages)

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